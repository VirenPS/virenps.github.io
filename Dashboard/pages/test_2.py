import pandas as pd
import plotly.express as px

# Create dataset
data = {
    "year": [2015, 2016, 2017, 2018, 2019],
    "lifeexp": [75, 74, 72, 70, 69],
    "state": ["kerala", "punjab", "karnataka", "andhra", "odisha"],
    "ratio": [74, 73.9, 71.5, 69.8, 69],
}

# Create dataframe
df = pd.DataFrame(data)

# Create Line plot
fig = px.line(df, x=df["year"], y=df["lifeexp"])

# Add Scatter plot
fig.add_scatter(x=df["year"], y=df["ratio"], mode="markers")

# Display the plot
# fig.show()
