import pandas as pd
import numpy as np
import plotly.graph_objects as go

def to_decimal_year(x):
    dt = pd.to_datetime(x)
    year = dt.dt.year

    year_start = pd.to_datetime(year.astype(str) + '-01-01')
    next_year_start = pd.to_datetime((year + 1).astype(str) + '-01-01')
    tp_date = pd.to_datetime(x)
    return (dt - year_start) / (next_year_start - year_start) + year

dataset = pd.read_feather('German_Energy_Consumption_20181001_to_20261108.feather')
df_plot = dataset.copy()
dims = dataset.shape
df_plot['tof'] = dataset['Timestamp'].dt.hour + dataset['Timestamp'].dt.minute / 60
df_plot['dec_year'] = to_decimal_year(dataset['Timestamp'].dt.date)
df_plot = df_plot.drop(['Timestamp'], axis = 1)
df_plot['timediff'] = 0.25

df_plot.loc[1:(dims[0] - 1), 'timediff'] = df_plot.loc[1:(dims[0] - 1), 'tof'].to_numpy() - df_plot.loc[0:(dims[0] - 2), 'tof'].to_numpy()
df_plot.loc[df_plot['timediff'] == -23.75, 'timediff'] = 0.25
backw_mask = df_plot['timediff'] == -0.75
idx_backw = backw_mask[backw_mask].index
for i in reversed(range(0, idx_backw.shape[0])):
    idx = idx_backw[i]
    df_plot.loc[(idx - 4):(idx - 1), 'Value'] = (df_plot.loc[idx:(idx + 3), 'Value'].to_numpy() + df_plot.loc[(idx - 4):(idx - 1), 'Value'].to_numpy()) / 2
    df_plot = df_plot.drop(range(idx, idx + 4), axis = 0)
        
df_plot = df_plot.reset_index(drop = True)

dims = df_plot.shape
df_plot.loc[1:(dims[0] - 1), 'timediff'] = df_plot.loc[1:(dims[0] - 1), 'tof'].to_numpy() - df_plot.loc[0:(dims[0] - 2), 'tof'].to_numpy()
df_plot.loc[df_plot['timediff'] == -23.75, 'timediff'] = 0.25
forw_mask = df_plot['timediff'] == 1.25
idx_forw = forw_mask[forw_mask].index
for i in range(0, idx_forw.shape[0]):
    x = np.array([2.00, 2.25, 2.5, 2.75])
    xp = np.array([1.75, 3.00])
    yp = np.array([df_plot.loc[idx_forw[i].item() - 1, 'Value'].item(), df_plot.loc[idx_forw[i].item(), 'Value'].item()])
    val_interp = np.interp(x = x, xp = xp, fp = yp)
    df_add = pd.DataFrame({
        'Value': val_interp,
        'tof': x,
        'dec_year': df_plot.loc[idx_forw[i].item(), 'dec_year'].item(),
        'timediff': 0.25
    })
    df_plot = pd.concat([df_plot, df_add], axis = 0)

df_plot = (
    df_plot
        .drop(['timediff'], axis = 1)
        .sort_values(['dec_year', 'tof'], ascending = [True, True])
        .reset_index(drop = True)
)

nday = len(df_plot.dec_year.unique())
ntime = len(df_plot.tof.unique())
values = df_plot.Value.to_numpy().reshape(nday, ntime) / 1000
tof = df_plot.tof.to_numpy().reshape(nday, ntime)
date = df_plot.dec_year.to_numpy().reshape(nday, ntime)

fig = go.Figure(data = [go.Surface(z = values, x = date, y = tof, colorscale = "inferno")])
fig.update_layout(showlegend = False)
fig.update_traces(showscale = False)
fig.update_layout(
    scene = dict(
        xaxis = dict(autorange = "reversed"),
        yaxis = dict(autorange = "reversed")
    )
)
fig.update_layout(
    title = 'Energy Consumption Germany',
    scene = dict(
        aspectmode = "cube",
        xaxis = dict(
            title = "Date",
            backgroundcolor = "white",
            gridcolor = "lightgrey",
            zerolinecolor = "lightgrey"
        ),
        yaxis = dict(
            title = "Time of day",
            backgroundcolor = "white",
            gridcolor = "lightgrey",
            zerolinecolor = "lightgrey"
        ),
        zaxis = dict(
            title = "GWh",
            backgroundcolor = "white",
            gridcolor = "lightgrey",
            zerolinecolor = "lightgrey"
        )
    ),
    paper_bgcolor = "white",
    plot_bgcolor = "white"
)

""" fig.update_layout(
    scene=dict(
        xaxis=dict(
            title="",
            showticklabels=False,
            ticks="",
            showspikes=False
        ),
        yaxis=dict(
            title="",
            showticklabels=False,
            ticks="",
            showspikes=False
        ),
        zaxis=dict(
            title="",
            showticklabels=False,
            ticks="",
            showspikes=False
        )
    )
) """

fig.show()
