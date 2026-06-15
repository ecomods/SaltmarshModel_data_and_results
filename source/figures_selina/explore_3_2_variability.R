# Title: Explore Figure 3.2 - two kinds of variability
# Date: 2026-06-15
# Author: Selina Baldauf
# Purpose: Two alternative views of the static community traits. Figure A shows
#   variability among plants WITHIN one replicate; Figure B shows variability
#   BETWEEN the 10 replicates. PFTs only (no community) for now.

# Libraries and setup ---------------------------------------------------------
source("source/figures_selina/figures_config.R")

metric_labels <- c(
  volume_per_plant = "Biovolume per plant [m³]",
  h_ag = "Aboveground height [m]",
  ag_bg_ratio = "AG/BG ratio [-]",
  num_plants = "Number of plants"
)

# Load data -------------------------------------------------------------------
# One row per plant per timestep per replicate. Mature plants, PFTs 1-4, static
# salinities. plant_uid is unique per plant within a replicate.
plants <- read_csv(path_comm_static, show_col_types = FALSE) |>
  add_derived_metrics() |>
  filter(
    pfts == "all",
    age >= 864000,
    pft %in% pft_levels,
    salinity %in% sal_static
  )


# =============================================================================
# FIGURE A: variability among plants WITHIN one representative replicate
# =============================================================================

# Step 1: pick one representative replicate per salinity --------------------
# "Representative" = the run whose total community biovolume (summed per
# timestep, then median over time) is closest to the median across the 10 runs.
total_per_timestep <- plants |>
  summarise(total = sum(volume), .by = c(salinity, n, time))

total_per_replicate <- total_per_timestep |>
  summarise(total = median(total), .by = c(salinity, n))

representative <- total_per_replicate |>
  mutate(distance = abs(total - median(total)), .by = salinity) |>
  slice_min(distance, n = 1, by = salinity, with_ties = FALSE) |>
  select(salinity, n)

plants_rep <- plants |>
  semi_join(representative, by = c("salinity", "n"))

# Step 2: one value per plant (median and max over its lifetime) -------------
# Long format so the three traits are handled together.
trait_long <- plants_rep |>
  rename(volume_per_plant = volume) |>
  pivot_longer(
    c(volume_per_plant, h_ag, ag_bg_ratio),
    names_to = "metric",
    values_to = "value"
  )

per_plant <- trait_long |>
  summarise(
    plant_median = median(value),
    plant_max = max(value),
    .by = c(metric, salinity, pft, plant_uid)
  )

# Step 3: number of plants over time (its within-replicate variability) ------
# For num_plants there is no per-plant value, so its within-run variability is
# the spread of the count across the timesteps of the representative run.
count_over_time <- plants_rep |>
  count(salinity, pft, time, name = "num_plants")

# Step 4: assemble one table per version (median, max) -----------------------
# Each row is one observation to be shown as a box: a plant (traits) or a
# timestep (num_plants).
figA_median <- bind_rows(
  per_plant |> select(metric, salinity, pft, value = plant_median),
  count_over_time |>
    mutate(metric = "num_plants") |>
    select(metric, salinity, pft, value = num_plants)
) |>
  mutate(
    metric = factor(
      metric,
      levels = names(metric_labels),
      labels = metric_labels
    ),
    pft = factor(pft, levels = pft_levels),
    salinity = factor(salinity, levels = sal_static)
  )

figA_max <- bind_rows(
  per_plant |> select(metric, salinity, pft, value = plant_max),
  count_over_time |>
    mutate(metric = "num_plants") |>
    select(metric, salinity, pft, value = num_plants)
) |>
  mutate(
    metric = factor(
      metric,
      levels = names(metric_labels),
      labels = metric_labels
    ),
    pft = factor(pft, levels = pft_levels),
    salinity = factor(salinity, levels = sal_static)
  )

# Step 5: plot (one boxplot version per per-plant statistic) -----------------
pA_median <- ggplot(figA_median, aes(x = salinity, y = value, fill = pft)) +
  geom_boxplot(
    linewidth = 0.3,
    outlier.size = 0.4,
    position = position_dodge(width = 0.8)
  ) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_fill_manual(
    values = pft_colors,
    name = NULL,
    labels = paste("PFT", pft_levels)
  ) +
  labs(
    x = "Salinity [ppt]",
    y = NULL,
    caption = "Within one representative replicate. Traits: per-plant MEDIAN size. num_plants: count over time."
  ) +
  theme_manuscript() +
  theme(legend.position = "bottom")

pA_max <- ggplot(figA_max, aes(x = salinity, y = value, fill = pft)) +
  geom_boxplot(
    linewidth = 0.3,
    outlier.size = 0.4,
    position = position_dodge(width = 0.8)
  ) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_fill_manual(
    values = pft_colors,
    name = NULL,
    labels = paste("PFT", pft_levels)
  ) +
  labs(
    x = "Salinity [ppt]",
    y = NULL,
    caption = "Within one representative replicate. Traits: per-plant MAX size. num_plants: count over time."
  ) +
  theme_manuscript() +
  theme(legend.position = "bottom")

print(pA_median)
print(pA_max)


# =============================================================================
# FIGURE B: variability BETWEEN the 10 replicates
# =============================================================================

# Step 1: one value per plant (median over life), for ALL replicates ---------
per_plant_all <- plants |>
  rename(volume_per_plant = volume) |>
  pivot_longer(
    c(volume_per_plant, h_ag, ag_bg_ratio),
    names_to = "metric",
    values_to = "value"
  ) |>
  summarise(
    plant_median = median(value),
    .by = c(metric, salinity, pft, n, plant_uid)
  )

# Step 2: one value per replicate = median across that run's plants ----------
trait_per_replicate <- per_plant_all |>
  summarise(value = median(plant_median), .by = c(metric, salinity, pft, n))

# Step 3: num_plants per replicate = median over time of the count -----------
count_per_replicate <- plants |>
  count(salinity, pft, n, time, name = "num_plants") |>
  summarise(value = median(num_plants), .by = c(salinity, pft, n)) |>
  mutate(metric = "num_plants")

# Step 4: assemble (one row per replicate) -----------------------------------
figB <- bind_rows(trait_per_replicate, count_per_replicate) |>
  mutate(
    metric = factor(
      metric,
      levels = names(metric_labels),
      labels = metric_labels
    ),
    pft = factor(pft, levels = pft_levels),
    salinity = factor(salinity, levels = sal_static)
  )

# Step 5: plot (the 10 replicate values + a median crossbar) -----------------
pB <- ggplot(figB, aes(x = salinity, y = value, colour = pft)) +
  geom_point(
    position = position_jitterdodge(jitter.width = 0.15, dodge.width = 0.7),
    size = 0.9,
    alpha = 0.7
  ) +
  stat_summary(
    fun = median,
    geom = "crossbar",
    width = 0.5,
    linewidth = 0.3,
    position = position_dodge(width = 0.7),
    show.legend = FALSE
  ) +
  facet_wrap(~metric, scales = "free_y", nrow = 2) +
  scale_colour_manual(
    values = pft_colors,
    name = NULL,
    labels = paste("PFT", pft_levels)
  ) +
  labs(
    x = "Salinity [ppt]",
    y = NULL,
    caption = "Each dot is one replicate (n = 10); crossbar = median across replicates."
  ) +
  theme_manuscript() +
  theme(legend.position = "bottom")

print(pB)

# Save (uncomment) ------------------------------------------------------------
dir.create(path_figures, showWarnings = FALSE, recursive = TRUE)
ggsave(
  file.path(path_figures, "explore_3_2_A_within_median.png"),
  pA_median,
  width = 7,
  height = 5.5,
  dpi = 300
)
ggsave(
  file.path(path_figures, "explore_3_2_A_within_max.png"),
  pA_max,
  width = 7,
  height = 5.5,
  dpi = 300
)
ggsave(
  file.path(path_figures, "explore_3_2_B_between.png"),
  pB,
  width = 7,
  height = 5.5,
  dpi = 300
)
