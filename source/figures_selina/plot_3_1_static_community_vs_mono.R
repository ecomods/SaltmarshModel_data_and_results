# Title: Figure 3.1 - static community vs monoculture biovolume
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: Total biovolume per salinity, community (stacked PFTs) vs each
#   monoculture (hatched). Reads the combined raw data and summarises below.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")
library(ggpattern)

# Load data -------------------------------------------------------------------
# Community = mixed setup (pfts == "all"); monoculture PFT is stored in pfts.
# Filters: mature plants only (age >= 10 days), PFTs 1-4, static salinities.
comm <- read_csv(path_comm_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  filter(pfts == "all", age >= 864000, pft %in% pft_levels, salinity %in% sal_static)
mono <- read_csv(path_mono_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  mutate(pft = as.integer(pfts)) |>
  filter(age >= 864000, pft %in% pft_levels, salinity %in% sal_static)

# Functions -------------------------------------------------------------------
# Median total biovolume per salinity x PFT:
# sum per timestep -> median over time per replicate -> median across replicates.
median_total_biovolume <- function(df) {
  df |>
    summarise(total_volume = sum(volume), .by = c(salinity, pft, n, time)) |>
    summarise(rep_median = median(total_volume), .by = c(salinity, pft, n)) |>
    summarise(value = median(rep_median), .by = c(salinity, pft))
}

# Fill the salinity x PFT grid so missing combinations (e.g. dead PFTs) show 0.
complete_grid <- function(summary_df) {
  expand_grid(salinity = sal_static, pft = pft_levels) |>
    left_join(summary_df, by = c("salinity", "pft")) |>
    mutate(value = coalesce(value, 0), pft = factor(pft, levels = pft_levels))
}

# Prepare ---------------------------------------------------------------------
# `bar` is the discrete x slot: one "community" slot (its four PFT rows stack)
# plus one slot per monoculture PFT.
bar_data <- bind_rows(
  complete_grid(median_total_biovolume(comm)) |>
    mutate(setup = "community", bar = "community"),
  complete_grid(median_total_biovolume(mono)) |>
    mutate(setup = "monoculture", bar = paste("PFT", pft))
) |>
  mutate(
    setup = factor(setup, levels = c("community", "monoculture")),
    bar = factor(bar, levels = c("community", paste("PFT", pft_levels)))
  )

# Plot ------------------------------------------------------------------------
# Faceting by salinity + a discrete x lets ggplot handle the spacing: rows that
# share a slot stack (community), the rest sit side by side (monocultures).
p <- ggplot(bar_data, aes(x = bar, y = value, fill = pft, pattern = setup)) +
  geom_col_pattern(
    position = position_stack(reverse = TRUE),
    colour = "black", linewidth = 0.2,
    pattern_colour = NA, pattern_fill = "black",
    pattern_density = 0.25, pattern_spacing = 0.02, pattern_angle = 45
  ) +
  facet_wrap(~salinity, nrow = 1, labeller = labeller(salinity = ~ paste0(.x, " ppt"))) +
  scale_fill_manual(values = pft_colors, name = NULL, labels = paste("PFT", pft_levels)) +
  scale_pattern_manual(values = c(community = "none", monoculture = "stripe"), name = NULL) +
  labs(x = NULL, y = expression("Total biovolume [m"^3 * "]")) +
  guides(
    fill = guide_legend(override.aes = list(pattern = "none"), order = 1),
    pattern = guide_legend(override.aes = list(fill = "white", pattern_density = 0.25), order = 2)
  ) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linetype = "dotted", linewidth = 0.3, colour = "grey70"))

print(p)

# Save (uncomment) ------------------------------------------------------------
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_3_1_static_community_vs_mono_R.png"),
#        p, width = 5, height = 3.5, dpi = 300)
