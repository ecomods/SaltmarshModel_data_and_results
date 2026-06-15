# Shared setup for the figure scripts: paths, colours, theme, and the few
# helpers used by more than one script.
# Run the scripts with the working directory at the project root so the
# relative paths below resolve.

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(readr)
})

# Combined raw tables (one row per plant per timestep), from 01_read_raw_data.py.
path_comm_static  <- "data/community/static/raw_data.csv"
path_comm_dynamic <- "data/community/dynamic/raw_data.csv"
path_mono_static  <- "data/monoculture/static/raw_data.csv"

# Where to save figures (kept separate from the manuscript figures/).
path_figures <- "figures/figures_selina"

# Scenario / PFT order.
sal_static     <- c(35, 70, 105, 140)
sal_dyn        <- c(35, 70, 105)
pft_levels     <- 1:4
variant_levels <- c("V0", "V1", "V2")

# Colours: seaborn "colorblind" palette for PFT 1-4, plus the dynamic variants.
pft_colors        <- c("1" = "#0173b2", "2" = "#de8f05", "3" = "#029e73", "4" = "#d55e00")
variant_colors    <- c(V0 = "grey25", V1 = "#8c510a", V2 = "#2171b5")
variant_linetypes <- c(V0 = "dashed", V1 = "solid", V2 = "solid")

theme_manuscript <- function(base_size = 8) {
  theme_bw(base_size = base_size) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      strip.background = element_rect(fill = "grey92", colour = NA)
    )
}

# Plant volume, AG/BG ratio and PFT from the raw columns. (The raw `volume`
# column already equals this cylinder formula; we recompute it to be explicit.)
# pft is the number in the plant id, e.g. "Saltmarsh_1_000123" -> 1.
add_derived_metrics <- function(df) {
  df %>%
    mutate(
      ag_volume   = pi * r_ag^2 * h_ag,
      bg_volume   = pi * r_bg^2 * h_bg,
      volume      = ag_volume + bg_volume,
      ag_bg_ratio = ag_volume / bg_volume,
      pft = as.integer(sub("^[^_]+_([0-9]+)_.*$", "\\1", plant))
    )
}
