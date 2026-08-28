# nature_chord.R -- grouped chord diagram for journal figures.
#
# Why R and not matplotlib, in a repo whose other assets are Python: the hard
# part of a chord diagram is not style, it is geometry -- sector allocation,
# gap budgeting, ribbon Bezier control points, arrow heads that follow the arc.
# circlize solves all of that and is the de-facto reference implementation.
# Everything else in this file is the part circlize deliberately leaves to you,
# which is also the part that decides whether the figure is readable.
#
# Usage
# -----
#   source("nature_chord.R")
#
#   chord_config$input      <- "edges.csv"     # long edge list
#   chord_config$from       <- "source"
#   chord_config$to         <- "target"
#   chord_config$value      <- "weight"
#   chord_config$category   <- "sign"          # optional: colours the ribbons
#   chord_config$output     <- "fig3_a_chord"  # writes .pdf and .png
#   nature_chord(chord_config)
#
#   Rscript nature_chord.R          # self-test on synthetic data, writes
#                                   # demo_chord.pdf / demo_chord.png
#
# Design rules encoded here
# -------------------------
# * A chord diagram is readable at roughly 10-15 sectors and stops being one at
#   30+. Above that it is a decorative annulus: nobody can trace a ribbon from
#   end to end, and the figure has silently become a texture. The honest fixes
#   are aggregation (group the nodes and draw the group-level matrix) or a
#   different chart -- a Sankey if the flow is staged, a heatmap matrix if the
#   claim is really "which pairs are large". `max_sectors` warns rather than
#   refusing, because a grouped diagram with tiny labelled sectors can work
#   when the GROUPS are the unit the reader tracks.
# * Small ribbons are hidden by setting their alpha to zero, NOT by dropping
#   their rows. Dropping rows shrinks the sectors, so the arc lengths stop
#   being the totals the caption claims they are. Transparent ribbons keep
#   every sector at its true size while removing the haze that buries the
#   flows the figure is about.
# * Ribbon opacity carries magnitude, on a sqrt scale, so mid-sized flows stay
#   visible instead of being crushed by one dominant link.
# * Ribbon COLOUR carries a category (direction, sign, class) -- never a second
#   continuous variable. Chords already spend position and width; a continuous
#   colour ramp on top of that is a third channel nobody reads.
# * cell.padding = 0 is mandatory when small sectors exist: the default padding
#   is larger than a small sector, and circlize silently drops it.
# * Vector PDF is the deliverable. A 600-dpi PNG is a preview, not final
#   artwork -- see references/spec.md.
#
# Nothing here depends on a specific project or discipline.

suppressPackageStartupMessages({
  library(circlize)
})

# --------------------------------------------------------------------------
# Configuration. Copy, edit the fields you need, pass to nature_chord().
# --------------------------------------------------------------------------

chord_config <- list(
  # --- input ---------------------------------------------------------
  input      = NULL,      # path to a long edge list CSV, or a data.frame
  from       = "from",
  to         = "to",
  value      = "value",
  category   = NULL,      # optional column naming a ribbon class

  # --- grouping (OPTIONAL, off by default) ---------------------------
  # Ungrouped is the default: nodes sorted by name, one uniform gap, no group
  # arcs and no group labels. That is the right default because a grouping
  # invented by the plotting code is a claim about the data's structure, and
  # nothing here knows whether your node names encode one.
  #
  # Turn it on when the nodes really do fall into blocks the reader should
  # see, in either of two ways:
  #
  #   group     = "sector"        # a column in the edge table, or
  #   group_fun = function(node) sub("\\..*$", "", node)   # derive from the name
  #
  # Once on, nodes are ordered by group then within group, and the gap budget
  # follows: a small gap inside a group, a large one between. That single
  # difference is what lets a reader see blocks instead of a picket fence.
  group      = NULL,      # column naming each node's group
  group_fun  = NULL,      # or a function node -> group name
  gap_within = 0.6,       # degrees, between nodes of the same group
  gap_between = 3.0,      # degrees, between groups -- and the uniform gap
                          # used when there is no grouping at all

  # --- what to draw --------------------------------------------------
  # Ribbons below this quantile of value are drawn fully transparent. Their
  # rows stay in the matrix, so sector sizes remain the true totals.
  hide_below_quantile = 0.90,
  alpha_range = c(0.15, 0.75),
  label_min_degrees = 1.5,   # sectors narrower than this get no node label
  max_sectors = 15,          # warn above this
  directional = TRUE,        # draw arrows and a height step at the target end

  # --- colour --------------------------------------------------------
  # Sector colours: a named vector group -> hex, or NULL for a generated ramp.
  group_colors = NULL,
  # Ribbon colours by category level: a named vector, or NULL for the default
  # two-class pair below.
  category_colors = c("positive" = "#015696", "negative" = "#C84747"),
  default_link_color = "#015696",

  # --- output --------------------------------------------------------
  output      = "chord",
  width_mm    = 88,       # 88 (single column) or 180 (double)
  label_pt    = 6.5,      # LANDED point size for node labels
  group_pt    = 7.5,      # LANDED point size for group labels
  png_preview = TRUE
)


# --------------------------------------------------------------------------
# Type sizing
#
# circlize takes `cex`, a MULTIPLIER on the device's base point size, while a
# journal constrains landed points. Fixing cex directly is how chord labels end
# up at whatever size the device happened to default to. Set the device base
# size once, then cex = landed_pt / base_pt.
# --------------------------------------------------------------------------

BASE_PT <- 7

pt_to_cex <- function(pt) pt / BASE_PT


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

.pick_font <- function() {
  ok <- tryCatch({
    suppressPackageStartupMessages(library(extrafont))
    loadfonts(device = "pdf", quiet = TRUE)
    "Arial" %in% fonts()
  }, error = function(e) FALSE)
  if (isTRUE(ok)) "Arial" else "sans"
}

# Ordered ramp for however many groups exist. Deliberately not a rainbow: the
# groups on a chord diagram are usually nominal, and the ramp's only job is to
# make adjacent blocks distinguishable.
.group_ramp <- function(n) {
  base <- c("#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
            "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD")
  if (n <= length(base)) return(base[seq_len(n)])
  grDevices::colorRampPalette(base)(n)
}

.with_alpha <- function(col, alpha) {
  m <- grDevices::col2rgb(col) / 255
  grDevices::rgb(m[1, ], m[2, ], m[3, ], alpha = alpha)
}


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

nature_chord <- function(cfg = chord_config) {
  stopifnot(!is.null(cfg$input))

  df <- if (is.data.frame(cfg$input)) cfg$input else
    utils::read.csv(cfg$input, stringsAsFactors = FALSE)

  links <- data.frame(
    from  = as.character(df[[cfg$from]]),
    to    = as.character(df[[cfg$to]]),
    value = as.numeric(df[[cfg$value]]),
    stringsAsFactors = FALSE
  )
  links$cat <- if (!is.null(cfg$category)) as.character(df[[cfg$category]]) else NA_character_
  links <- links[is.finite(links$value) & links$value > 0, , drop = FALSE]
  if (!nrow(links)) stop("nature_chord(): no positive-weight edges")

  # --- node table: group, then order ---------------------------------
  nodes <- sort(unique(c(links$from, links$to)))
  grouped <- !is.null(cfg$group) || !is.null(cfg$group_fun)

  grp <- if (!is.null(cfg$group)) {
    map <- stats::setNames(as.character(df[[cfg$group]]),
                           as.character(df[[cfg$from]]))
    map2 <- stats::setNames(as.character(df[[cfg$group]]),
                            as.character(df[[cfg$to]]))
    out <- map[nodes]
    out[is.na(out)] <- map2[nodes][is.na(out)]
    out
  } else if (!is.null(cfg$group_fun)) {
    vapply(nodes, cfg$group_fun, character(1))
  } else {
    nodes                       # ungrouped: every node is its own block
  }
  meta <- data.frame(node = nodes, group = as.character(grp),
                     stringsAsFactors = FALSE)
  meta <- meta[order(meta$group, meta$node), , drop = FALSE]

  if (nrow(meta) > cfg$max_sectors) {
    hint <- if (grouped)
      sprintf("Either aggregate to the %d groups and draw the group-level matrix, or use a Sankey / heatmap instead.",
              length(unique(meta$group)))
    else
      "Either define a grouping (see chord_config$group / $group_fun) and aggregate to it, or use a Sankey / heatmap instead."
    message(sprintf(
      "nature_chord(): %d sectors. A chord diagram stops being traceable above ~%d. %s Drawing anyway.",
      nrow(meta), cfg$max_sectors, hint))
  }

  links$from <- factor(links$from, levels = meta$node)
  links$to   <- factor(links$to,   levels = meta$node)
  links <- links[order(links$from, links$to), , drop = FALSE]

  # --- ribbon colour: category -> hue, magnitude -> alpha ------------
  cutoff <- stats::quantile(links$value, cfg$hide_below_quantile)
  visible <- links$value > cutoff

  base_col <- rep(cfg$default_link_color, nrow(links))
  if (!is.null(cfg$category) && !is.null(cfg$category_colors)) {
    hit <- links$cat %in% names(cfg$category_colors)
    base_col[hit] <- unname(cfg$category_colors[links$cat[hit]])
  }

  rng <- range(links$value)
  a_lo <- cfg$alpha_range[1]; a_hi <- cfg$alpha_range[2]
  alpha <- if (diff(rng) == 0) rep(mean(cfg$alpha_range), nrow(links)) else
    a_lo + (a_hi - a_lo) * sqrt((links$value - rng[1]) / diff(rng))
  alpha[!visible] <- 0
  link_col <- .with_alpha(base_col, alpha)

  message(sprintf("nature_chord(): %d edges, %d drawn (top %.0f%% by value), %d sectors%s",
                  nrow(links), sum(visible),
                  100 * (1 - cfg$hide_below_quantile), nrow(meta),
                  if (grouped) sprintf(" in %d groups", length(unique(meta$group)))
                  else " (ungrouped)"))

  # --- sector colour --------------------------------------------------
  groups <- unique(meta$group)
  gcol <- cfg$group_colors
  if (is.null(gcol)) gcol <- stats::setNames(.group_ramp(length(groups)), groups)
  grid_col <- stats::setNames(unname(gcol[meta$group]), meta$node)

  # --- gap budget -----------------------------------------------------
  # Grouped: small gap within a group, large between. Ungrouped: one uniform
  # gap, because there is no block structure for a varying gap to encode.
  gaps <- if (grouped) {
    nxt <- c(meta$group[-1], meta$group[1])
    ifelse(meta$group == nxt, cfg$gap_within, cfg$gap_between)
  } else {
    rep(cfg$gap_between, nrow(meta))
  }

  font_family <- .pick_font()
  in_w <- cfg$width_mm / 25.4

  .draw <- function() {
    par(ps = BASE_PT, family = font_family, mar = c(0, 0, 0, 0))
    circos.clear()
    circos.par(
      start.degree = 90,
      gap.degree = gaps,
      track.margin = c(0.005, 0.005),
      cell.padding = c(0, 0, 0, 0),   # REQUIRED: default padding hides small sectors
      points.overflow.warning = FALSE
    )

    chordDiagram(
      links[, c("from", "to", "value")],
      grid.col = grid_col,
      col = link_col,
      transparency = 0,               # alpha already baked into col
      annotationTrack = "grid",
      preAllocateTracks = if (grouped) list(
        list(track.height = 0.14),    # 1: group labels
        list(track.height = 0.04),    # 2: group arcs
        list(track.height = 0.06)     # 3: node labels
      ) else list(
        list(track.height = 0.09)     # 1: node labels only
      ),
      link.sort = TRUE,
      link.decreasing = TRUE,
      directional = if (isTRUE(cfg$directional)) 1 else 0,
      direction.type = if (isTRUE(cfg$directional))
        c("diffHeight", "arrows") else "diffHeight",
      link.arr.type = "big.arrow",
      diffHeight = -0.04,
      reduce = 0
    )

    for (g in if (grouped) groups else character(0)) {
      idx <- meta$node[meta$group == g]
      if (!length(idx)) next
      highlight.sector(sector.index = idx, track.index = 2,
                       col = unname(gcol[g]), text = "", border = NA)
      highlight.sector(sector.index = idx, track.index = 1,
                       col = NA, border = NA, text = g,
                       cex = pt_to_cex(cfg$group_pt), text.col = "black",
                       # bending, not radial: a group label spans many degrees,
                       # and a radial one lies across its neighbours' node
                       # labels at every group boundary
                       facing = "bending.outside", niceFacing = TRUE,
                       font = 2, family = font_family)
    }

    # Node labels, suppressed on sectors too narrow to hold one. A label
    # wider than its own sector does not identify anything -- it just points
    # at the neighbourhood, and three of them overlap into a smear.
    circos.track(track.index = if (grouped) 3 else 1, panel.fun = function(x, y) {
      si <- get.cell.meta.data("sector.index")
      d <- abs(get.cell.meta.data("cell.end.degree") -
               get.cell.meta.data("cell.start.degree"))
      if (d > 180) d <- 360 - d
      if (d > cfg$label_min_degrees) {
        circos.text(mean(get.cell.meta.data("xlim")),
                    mean(get.cell.meta.data("ylim")), si,
                    facing = "clockwise", niceFacing = TRUE,
                    adj = c(0.5, 0.5), cex = pt_to_cex(cfg$label_pt),
                    col = "black", family = font_family)
      }
    }, bg.border = NA)

    circos.clear()
  }

  # PDF is the deliverable; PNG is a preview only.
  grDevices::pdf(paste0(cfg$output, ".pdf"), width = in_w, height = in_w,
                 pointsize = BASE_PT, family = font_family, useDingbats = FALSE)
  .draw()
  grDevices::dev.off()

  if (isTRUE(cfg$png_preview)) {
    grDevices::png(paste0(cfg$output, ".png"), width = in_w, height = in_w,
                   units = "in", res = 300, pointsize = BASE_PT)
    .draw()
    grDevices::dev.off()
  }

  invisible(list(meta = meta, links = links, cutoff = cutoff,
                 n_drawn = sum(visible)))
}


# --------------------------------------------------------------------------
# Companion legend
#
# The ribbon categories cannot be read off the diagram: a chord has no axis and
# circlize draws no legend. Export one as its own file and place it at
# assembly, the same way nature_style::export_legend does for a Python panel.
# --------------------------------------------------------------------------

chord_legend <- function(items, output = "chord_legend", width_mm = 30,
                         pt = 6.5, alpha = 0.7) {
  font_family <- .pick_font()
  in_w <- width_mm / 25.4
  n <- length(items)
  in_h <- (n * 4.2 + 2) / 25.4

  .draw <- function() {
    par(ps = BASE_PT, family = font_family, mar = c(0, 0, 0, 0))
    plot.new()
    plot.window(xlim = c(0, 1), ylim = c(0, n))
    for (i in seq_len(n)) {
      y <- n - i + 0.5
      rect(0.02, y - 0.28, 0.22, y + 0.28,
           col = .with_alpha(items[[i]], alpha), border = NA)
      text(0.28, y, names(items)[i], adj = c(0, 0.5),
           cex = pt_to_cex(pt), family = font_family)
    }
  }

  grDevices::pdf(paste0(output, ".pdf"), width = in_w, height = in_h,
                 pointsize = BASE_PT, family = font_family, useDingbats = FALSE)
  .draw()
  grDevices::dev.off()
  invisible(output)
}


# --------------------------------------------------------------------------
# Self-test: synthetic data only, no project files.
# --------------------------------------------------------------------------

if (sys.nframe() == 0L) {
  set.seed(11)
  groups <- paste0("G", 1:4)
  nodes <- unlist(lapply(seq_along(groups),
                         function(i) paste0(i, ".", 1:3)))
  n <- 90
  e <- data.frame(
    from = sample(nodes, n, replace = TRUE),
    to   = sample(nodes, n, replace = TRUE),
    weight = round(rlnorm(n, 4, 1.3)),
    sign = sample(c("positive", "negative"), n, replace = TRUE,
                  prob = c(0.7, 0.3)),
    stringsAsFactors = FALSE
  )
  e <- e[e$from != e$to, ]

  base <- chord_config
  base$input <- e
  base$value <- "weight"
  base$category <- "sign"
  base$hide_below_quantile <- 0.75

  # (a) the default path: ungrouped
  ungrouped <- base
  ungrouped$output <- "demo_chord_ungrouped"
  nature_chord(ungrouped)

  # (b) grouping opted into, here derived from the node name's prefix
  grouped <- base
  grouped$group_fun <- function(node) paste0("Group ", sub("\\..*$", "", node))
  grouped$output <- "demo_chord_grouped"
  nature_chord(grouped)

  chord_legend(as.list(base$category_colors), output = "demo_chord_legend")
  message("wrote demo_chord_ungrouped.*, demo_chord_grouped.*, demo_chord_legend.pdf")
}
