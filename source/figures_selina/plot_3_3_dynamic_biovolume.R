# Title: Figure 3.3 - dynamic biovolume grid
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: PFT biovolume over time for V0 (static), V1 (seasonal) and V2
#   (seasonal + tidal), with stacked totals per variant. Reads combined raw data.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")
library(patchwork)

# Load data -------------------------------------------------------------------
common_cols <- c("salinity", "variant", "version", "pft", "n", "time", "volume")

# V1 / V2 from the dynamic runs; variant is the suffix of the version label.
dyn <- read_csv(path_comm_dynamic, show_col_types = FALSE) |>
  add_derived_metrics() |>
  mutate(salinity = if_else(salinity == 10, 105, salinity),
         variant = str_remove(version, "^[0-9]+_")) |>
  filter(pfts == "all", age >= 864000, pft %in% pft_levels,
         salinity %in% sal_dyn, variant %in% c("V1", "V2")) |>
  select(all_of(common_cols))

# V0 from the static runs (restricted to the dynamic salinities).
v0 <- read_csv(path_comm_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  filter(pfts == "all", age >= 864000, pft %in% pft_levels, salinity %in% sal_dyn) |>
  mutate(variant = "V0", version = paste0(salinity, "_V0")) |>
  select(all_of(common_cols))

dyn_all <- bind_rows(v0, dyn) |> mutate(time_days = time / 86400)

# Summarise -------------------------------------------------------------------
# Stacked-bar values: sum per timestep -> median over time per replicate ->
# median across replicates.
bars <- dyn_all |>
  summarise(tv = sum(volume), .by = c(salinity, variant, pft, n, time)) |>
  summarise(rep_med = median(tv), .by = c(salinity, variant, pft, n)) |>
  summarise(median_value = median(rep_med), .by = c(salinity, variant, pft))

# Time-series values: per-timestep PFT total, median across replicates.
ts <- dyn_all |>
  summarise(tv = sum(volume), .by = c(version, pft, n, time_days)) |>
  summarise(value = median(tv), .by = c(version, pft, time_days)) |>
  separate(version, into = c("salinity", "variant"), sep = "_", remove = FALSE) |>
  mutate(salinity = as.integer(salinity))

# Shared y-limits from the time series (5% padding).
pad <- 0.05 * (max(ts$value) - min(ts$value))
y_lim <- c(min(ts$value) - pad, max(ts$value) + pad)

# Prepare ---------------------------------------------------------------------
# Facet-strip labels.
sal_lab <- function(s) factor(s, levels = sal_dyn, labels = paste0(sal_dyn, " ppt"))
ts <- ts |>
  mutate(salinity_lab = sal_lab(salinity),
         pft_lab = factor(pft, levels = pft_levels, labels = paste("PFT", pft_levels)),
         variant = factor(variant, levels = variant_levels))
bars <- bars |>
  mutate(salinity_lab = sal_lab(salinity),
         pft = factor(pft, levels = pft_levels),
         variant = factor(variant, levels = variant_levels),
         col = "Total")

# Plot ------------------------------------------------------------------------
p_lines <- ggplot(ts, aes(time_days, value, colour = variant, linetype = variant)) +
  geom_line(linewidth = 0.5) +
  facet_grid(salinity_lab ~ pft_lab) +
  scale_colour_manual(values = variant_colors, name = "Variant") +
  scale_linetype_manual(values = variant_linetypes, name = "Variant") +
  coord_cartesian(ylim = y_lim) +
  labs(x = "t [d]", y = expression("Total biovolume [m"^3 * "]")) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey90"))

p_bars <- ggplot(bars, aes(x = variant, y = median_value, fill = pft)) +
  geom_col(position = position_stack(reverse = TRUE), colour = "black", linewidth = 0.2, width = 0.8) +
  facet_grid(salinity_lab ~ col) +
  scale_fill_manual(values = pft_colors, name = NULL, labels = paste("PFT", pft_levels)) +
  coord_cartesian(ylim = y_lim) +
  labs(x = "Variant", y = NULL) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linetype = "dotted", linewidth = 0.3, colour = "grey80"))

p <- p_lines + p_bars +
  plot_layout(widths = c(4, 1.05), guides = "collect") &
  theme(legend.position = "bottom")

print(p)

# Save (uncomment) ------------------------------------------------------------
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_3_3_dynamic_biovolume_R.png"),
#        p, width = 8.3, height = 6.7, dpi = 300)
