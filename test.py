import pandas as pd

pf=pd.read_csv('上海商銀.csv')
print(pf)
pf=pf.drop(columns=["display_topic"])
print(pf)
pf.to_csv('上海商銀.csv', index=False)