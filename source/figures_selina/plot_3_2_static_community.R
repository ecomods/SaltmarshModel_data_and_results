# Figure 3.2: static community structure, 2x2 grid.
# Panels: biovolume per plant, aboveground height, AG/BG ratio, number of plants.
# Black = whole community, colours = PFTs. Reads combined raw data; summarises below.
# Error bars: plant-level metrics = min/max over individual plants;
# num_plants = min/max across replicate values. Run from the project root.

source("source/figures_selina/figures_config.R")

comm <- read_csv(path_comm_static, show_col_types = FALSE) %>%
  add_derived_metrics() %>%
  filter(pfts == "all", age >= 864000, pft %in% pft_levels, salinity %in% sal_static)

# Plant-level metric: median + min/max over individual plants.
# by_pft = FALSE gives the whole-community series.
summ_individuals <- function(df, metric, by_pft) {
  keys <- if (by_pft) c("salinity", "pft") else "salinity"
  df %>%
    group_by(across(all_of(keys))) %>%
    summarise(med = median(.data[[metric]]),
              lo  = min(.data[[metric]]),
              hi  = max(.data[[metric]]), .groups = "drop")
}

# Number of plants: count per timestep -> median over time per replicate ->
# min/max across replicates.
summ_num_plants <- function(df, by_pft) {
  keys <- if (by_pft) c("salinity", "pft") else "salinity"
  df %>%
    count(across(all_of(c(keys, "n", "time"))), name = "num_plants") %>%
    group_by(across(all_of(c(keys, "n")))) %>%
    summarise(rep_med = median(num_plants), .groups = "drop") %>%
    group_by(across(all_of(keys))) %>%
    summarise(med = median(rep_med), lo = min(rep_med), hi = max(rep_med), .groups = "drop")
}

plant_metrics <- c(volume_per_plant = "volume", h_ag = "h_ag", ag_bg_ratio = "ag_bg_ratio")

build_metric <- function(metric_name) {
  if (metric_name == "num_plants") {
    pft  <- summ_num_plants(comm, by_pft = TRUE)
    all_ <- summ_num_plants(comm, by_pft = FALSE)
  } else {
    col  <- plant_metrics[[metric_name]]
    pft  <- summ_individuals(comm, col, by_pft = TRUE)
    all_ <- summ_individuals(comm, col, by_pft = FALSE)
  }
  bind_rows(all_ %>% mutate(group = "community"),
            pft  %>% mutate(group = paste("PFT", pft))) %>%
    mutate(metric = metric_name)
}

metric_labels <- c(
  volume_per_plant = "Biovolume per plant [m³]",
  h_ag             = "Aboveground height [m]",
  ag_bg_ratio      = "AG/BG ratio [-]",
  num_plants       = "Number of plants"
)

plot_df <- bind_rows(lapply(names(metric_labels), build_metric)) %>%
  mutate(
    metric   = factor(metric, levels = names(metric_labels), labels = metric_labels),
    group    = factor(group, levels = c("community", paste("PFT", pft_levels))),
    salinity = factor(salinity, levels = sal_static)
  )

group_colors <- c("community" = "black", setNames(pft_colors, paste("PFT", pft_levels)))

p <- ggplot(plot_df, aes(x = salinity, y = med, colour = group)) +
  geom_pointrange(aes(ymin = lo, ymax = hi),
                  position = position_dodge(width = 0.6), size = 0.3, linewidth = 0.5) +
  facet_wrap(~ metric, scales = "free_y", nrow = 2) +
  scale_colour_manual(values = group_colors, name = NULL) +
  labs(x = "Salinity [ppt]", y = NULL) +
  theme_manuscript() +
  theme(panel.grid.major.y = element_line(linetype = "dotted", linewidth = 0.3, colour = "grey80"),
        legend.position = "bottom")

print(p)

# To save, uncomment:
# dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
# ggsave(file.path(path_figures, "plot_3_2_static_community_R.png"),
#        p, width = 7, height = 5.5, dpi = 300)
