/*
 * Draw a Chart.js chart from the JSON in data-module-chart:
 *   {"type": "line" | "bar", "labels": [...], "datasets": [{"label": "...", "data": [...]}]}
 * All the data comes from Python, this module only draws it.
 * Chart.js is served locally (assets/vendor), see webassets.yml
 */
ckan.module("api-tracking-chart", function ($) {
  "use strict";

  // Fixed order, max 2 series (validated for color blindness)
  var COLORS = ["#2a78d6", "#eb6834"];

  return {
    options: {
      chart: null,
    },

    initialize: function () {
      var chart = this.options.chart;
      if (!chart || typeof Chart === "undefined") {
        return;
      }
      var isBar = chart.type === "bar";
      var datasets = chart.datasets.map(function (dataset, i) {
        return {
          label: dataset.label,
          data: dataset.data,
          backgroundColor: COLORS[i],
          borderColor: isBar ? "#ffffff" : COLORS[i],
          borderWidth: 2,
          pointRadius: 0,
        };
      });

      new Chart(this.el.find("canvas")[0], {
        type: chart.type,
        data: { labels: chart.labels, datasets: datasets },
        options: {
          // Bars are horizontal: user names are long
          indexAxis: isBar ? "y" : "x",
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { display: datasets.length > 1 } },
          scales: {
            // Line charts: a few horizontal date labels, no vertical grid lines
            x: isBar
              ? { stacked: true, beginAtZero: true, ticks: { precision: 0 } }
              : { grid: { display: false }, ticks: { maxRotation: 0, maxTicksLimit: 8 } },
            y: { stacked: isBar, beginAtZero: true, ticks: { precision: 0 } },
          },
        },
      });
    },
  };
});
