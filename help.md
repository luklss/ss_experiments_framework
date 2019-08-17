### Need some help?

#### Interacting

You can interact with the graphs in a few ways:
* You can filter the data using the dropwdowns and the date bar below the plots. All filtering happens simultaneously for both graphs.
* You can also zoom in by selecting an area of a given chart, and double clicking in the graph to go back to the full view of the currently filtered data. But remember, zooming in this way **does not** filter the data.
* Lastly, you can also remove a given line in the chart by clicking on it at the legend.

#### Interpreting

The plot on the left (absolute metrics) should be straight forward, it simply shows the **absolute value** of the currently selected metric for the given period and filters.

The right plot can be a bit trickier. It shows much better (or worst) the experiment is performing when compared to the regular track (in percentage points) for the given metric selected. If, for instance, this ratio is 5 in a given day, that means that in that day the experiment track performed 5\% better than the regular. However, how do we know when this is statistically significant? This can get hairy very fast, and is out of this cope of this help, but here is a list of the other lines in the graph that can help us to have a bigger picture statistically:

* **performance**: the percentage difference between tracks for a given day as described above. A positive value means that the experiment has more of that metric.
* **7_day_average_performance**: the seven day average of the percentage difference between the tracks. This is the same as above but fluctuates less since is the average of the past week.
* **total_performance**: the percentage difference between tracks for the **totality** of the filtered data.
* **total_performance_upperbound** and **total_performance_lowerbound**: a statistical approximation of the confidence of the total performance measure given plus or minus 4 sigmas. This is an attempt in estimating how wrong we can be or how much we can trust that measure statistically speaking. For instance, every one can related to when in a presidential election we have a candidate that has 32 plus or minus 3 percent of the vote intentions. This is analogous.
