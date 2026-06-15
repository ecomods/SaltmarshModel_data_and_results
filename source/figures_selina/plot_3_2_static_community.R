# Title: Figure 3.2 - static community structure
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: Community structure vs salinity (biovolume per plant, height, AG/BG
#   ratio, plant count), for the whole community and each PFT.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")

# Load data -------------------------------------------------------------------
comm <- read_csv(path_comm_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  filter(
    pfts == "all",
    age >= 864000,
    pft %in% pft_levels,
    salinity %in% sal_static
  )

# Functions -------------------------------------------------------------------
# Plant-level metric: median + min/max over individual plants.
# by_pft = FALSE gives the whole-community series.
summarise_individuals <- function(df, metric, by_pft) {
  keys <- if (by_pft) c("salinity", "pft") else "salinity"
  df |>
    summarise(
      med = median(.data[[metric]]),
      lo = min(.data[[metric]]),
      hi = max(.data[[metric]]),
      .by = all_of(keys)
    )
}

# Number of plants: count per timestep -> median over time per replicate ->
# min/max across replicates.
summarise_num_plants <- function(df, by_pft) {
  keys <- if (by_pft) c("salinity", "pft") else "salinity"
  df |>
    count(across(all_of(c(keys, "n", "time"))), name = "num_plants") |>
    summarise(rep_med = median(num_plants), .by = all_of(c(keys, "n"))) |>
    summarise(
      med = median(rep_med),
      lo = min(rep_med),
      hi = max(rep_med),
      .by = all_of(keys)
    )
}

# One tidy table (community + per-PFT rows) for a single metric.
build_metric <- function(metric_name) {
  if (metric_name == "num_plants") {
    per_pft <- summarise_num_plants(comm, by_pft = TRUE)
    community <- summarise_num_plants(comm, by_pft = FALSE)
  } else {
    per_pft <- summarise_individuals(
      comm,
      plant_metrics[[metric_name]],
      by_pft = TRUE
    )
    community <- summarise_individuals(
      comm,
      plant_metrics[[metric_name]],
      by_pft = FALSE
    )
  }
  bind_rows(
    community |> mutate(group = "community"),
    per_pft |> mutate(group = paste("PFT", pft))
  ) |>
    mutate(metric = metric_name)
}

# Prepare ---------------------------------------------------------------------
plant_metrics <- c(
  volume_per_plant = "volume",
  h_ag = "h_ag",
  ag_bg_ratio = "ag_bg_ratio"
)

metric_labels <- c(
  volume_per_plant = "Biovolume per plant [m³]",
  h_ag = "Aboveground height [m]",
  ag_bg_ratio = "AG/BG ratio [-]",
  num_plants = "Number of plants"
)

community_metrics <- map(names(metric_labels), build_metric) |>
  list_rbind() |>
  mutate(
    metric = factor(
      metric,
      levels = names(metric_labels),
      labels = metric_labels
    ),
    group = factor(group, levels = c("community", paste("PFT", pft_levels))),
    salinity = factor(salinity, levels = sal_static)
  )

group_colors <- c(
  "community" = "black",
  setNames(pft_colors, paste("PFT", pft_levels))
)

# Plot ------------------------------------------------------------------------
p <- ggplot(community_metrics, aes(x = salinity, y = med, colour = group)) +
  geom_pointrange(
    aes(ymin = lo, ymax = hi),
    position = position_dodge(width = 0.6),
    size = 0.3,
    linewidth = 0.5
  ) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_colour_manual(values = group_colors, name = NULL) +
  labs(x = "Salinity [ppt]", y = NULL) +
  theme_manuscript() +
  theme(
    panel.grid.major.y = element_line(
      linetype = "dotted",
      linewidth = 0.3,
      colour = "grey80"
    ),
    legend.position = "bottom"
  )

print(p)

# Save (uncomment) ------------------------------------------------------------
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_3_2_static_community_R.png"),
#        p, width = 7, height = 5.5, dpi = 300)
