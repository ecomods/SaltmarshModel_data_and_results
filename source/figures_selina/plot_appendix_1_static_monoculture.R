# Title: Appendix Fig 1 - static monoculture structure
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: Monoculture structure vs salinity (biovolume per plant, height,
#   AG/BG ratio, plant count) per PFT, like Fig 3.2 but with no community series.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")

# Load data -------------------------------------------------------------------
# In monoculture runs the setup PFT is stored in pfts.
mono <- read_csv(path_mono_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  mutate(pft = as.integer(pfts)) |>
  filter(age >= 864000, pft %in% pft_levels, salinity %in% sal_static)

# Functions -------------------------------------------------------------------
# Plant-level metric: median + min/max over individual plants.
summarise_individuals <- function(df, metric) {
  df |>
    summarise(
      med = median(.data[[metric]]),
      lo = min(.data[[metric]]),
      hi = max(.data[[metric]]),
      .by = c(salinity, pft)
    )
}

# Number of plants: count per timestep -> median over time per replicate ->
# min/max across replicates.
summarise_num_plants <- function(df) {
  df |>
    count(salinity, pft, n, time, name = "num_plants") |>
    summarise(rep_med = median(num_plants), .by = c(salinity, pft, n)) |>
    summarise(med = median(rep_med), lo = min(rep_med), hi = max(rep_med), .by = c(salinity, pft))
}

build_metric <- function(metric_name) {
  if (metric_name == "num_plants") {
    summarise_num_plants(mono) |> mutate(metric = metric_name)
  } else {
    summarise_individuals(mono, plant_metrics[[metric_name]]) |> mutate(metric = metric_name)
  }
}

# Prepare ---------------------------------------------------------------------
plant_metrics <- c(volume_per_plant = "volume", h_ag = "h_ag", ag_bg_ratio = "ag_bg_ratio")

metric_labels <- c(
  volume_per_plant = "Biovolume per plant [m³]",
  h_ag             = "Aboveground height [m]",
  ag_bg_ratio      = "AG/BG ratio [-]",
  num_plants       = "Number of plants"
)

mono_metrics <- map(names(metric_labels), build_metric) |>
  list_rbind() |>
  mutate(
    metric = factor(metric, levels = names(metric_labels), labels = metric_labels),
    pft = factor(pft, levels = pft_levels),
    salinity = factor(salinity, levels = sal_static)
  )

# Plot ------------------------------------------------------------------------
p <- ggplot(mono_metrics, aes(x = salinity, y = med, colour = pft)) +
  geom_pointrange(aes(ymin = lo, ymax = hi),
                  position = position_dodge(width = 0.6), size = 0.3, linewidth = 0.5) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_colour_manual(values = pft_colors, name = NULL, labels = paste("PFT", pft_levels)) +
  labs(x = "Salinity [ppt]", y = NULL) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linetype = "dotted", linewidth = 0.3, colour = "grey80"),
        legend.position = "bottom")

print(p)

# Save (uncomment) ------------------------------------------------------------
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_appendix_1_static_monoculture_R.png"),
#        p, width = 7, height = 5.5, dpi = 300)
