import smardapi as api

api.allowed_filter_no()
api.allowed_region()
api.allowed_resolution()

api.specify(filter_no = 410, region = 'DE')
api.download(resolution = 'quarterhour', start = '2015-01-01', stop = '2026-11-08 23:59:00')

api.data.to_feather('German_Energy_Consumption_20150101_to_20261108.feather')

api.plot(legend = False)
