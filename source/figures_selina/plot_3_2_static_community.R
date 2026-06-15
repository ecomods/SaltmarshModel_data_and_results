# Title: Figure 3.2 (median + IQR) - static community structure
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: Reproduce the median + 25/75 percentile version of Figure 3.2, with
#   every summarisation step written out explicitly. Shows each PFT and the
#   whole community.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")

# Load data -------------------------------------------------------------------
# One row per plant per timestep per replicate. Keep mature plants (age >= 10
# days), PFTs 1-4 and the static salinities.
comm <- read_csv(path_comm_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  filter(pfts == "all", age >= 864000, pft %in% pft_levels, salinity %in% sal_static)

# Label every plant twice: once under its own PFT and once as "community". This
# way the same summaries below produce both the per-PFT and the community series.
comm <- bind_rows(
  comm |> mutate(group = paste("PFT", pft)),
  comm |> mutate(group = "community")
)

# Trait panels: median + 25/75 percentile over INDIVIDUAL plants --------------
# The manuscript pools all individual plants (every timestep, every replicate)
# and groups them only by salinity and group (PFT or community).

# Put the three trait metrics into long format: one row per plant per metric.
trait_long <- comm |>
  rename(volume_per_plant = volume) |>
  pivot_longer(c(volume_per_plant, h_ag, ag_bg_ratio),
               names_to = "metric", values_to = "value")

# Median and 25/75 percentiles across those individual plants.
trait_summary <- trait_long |>
  summarise(
    median = median(value),
    lower  = quantile(value, 0.25),
    upper  = quantile(value, 0.75),
    .by = c(metric, salinity, group)
  )

# Number of plants: median + 25/75 percentile ACROSS the 10 replicates --------

# Step 1: number of plants per timestep, within each replicate and group.
count_per_timestep <- comm |>
  count(salinity, group, n, time, name = "num_plants")

# Step 2: one typical count per replicate = median over the evaluation period.
count_per_replicate <- count_per_timestep |>
  summarise(rep_count = median(num_plants), .by = c(salinity, group, n))

# Step 3: median and 25/75 percentiles across the 10 replicates.
count_summary <- count_per_replicate |>
  summarise(
    median = median(rep_count),
    lower  = quantile(rep_count, 0.25),
    upper  = quantile(rep_count, 0.75),
    .by = c(salinity, group)
  ) |>
  mutate(metric = "num_plants")

# Combine for plotting --------------------------------------------------------
metric_labels <- c(
  volume_per_plant = "Biovolume per plant [m³]",
  h_ag = "Aboveground height [m]",
  ag_bg_ratio = "AG/BG ratio [-]",
  num_plants = "Number of plants"
)

group_colors <- c("community" = "black", setNames(pft_colors, paste("PFT", pft_levels)))

plot_data <- bind_rows(trait_summary, count_summary) |>
  mutate(
    metric = factor(metric, levels = names(metric_labels), labels = metric_labels),
    group = factor(group, levels = c("community", paste("PFT", pft_levels))),
    salinity = factor(salinity, levels = sal_static)
  )

# Plot ------------------------------------------------------------------------
p <- ggplot(plot_data, aes(x = salinity, y = median, colour = group)) +
  geom_pointrange(aes(ymin = lower, ymax = upper),
                  position = position_dodge(width = 0.6), size = 0.3, linewidth = 0.5) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_colour_manual(values = group_colors, name = NULL) +
  labs(x = "Salinity [ppt]", y = NULL) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linetype = "dotted", linewidth = 0.3, colour = "grey80"),
        legend.position = "bottom")

print(p)

# Save (uncomment) ------------------------------------------------------------
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_3_2_static_community_R.png"),
#        p, width = 7, height = 5.5, dpi = 300)
