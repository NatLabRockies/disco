import json
import pandas as pd
import ast

fn = r"C:\Users\SABRAHAM\Documents\GitHub\Tools\disco\disco\extensions\upgrade_simulation\upgrades\technical_catalog.json"

f = open(fn)
data = json.load(f)
f.close()

line_df = pd.DataFrame(data["line"])

line_df["rmatrix"] = line_df["rmatrix"].apply(lambda x: ast.literal_eval(x))
line_df["cmatrix"] = line_df["cmatrix"].apply(lambda x: ast.literal_eval(x))
line_df["xmatrix"] = line_df["xmatrix"].apply(lambda x: ast.literal_eval(x))

line_df = line_df.loc[line_df["line_placement"].notnull()]


xfmr_df = pd.DataFrame(data["transformer"])

xfmr_df["conns"] = xfmr_df["conns"].apply(lambda x: ast.literal_eval(x))
xfmr_df["kVs"] = xfmr_df["kVs"].apply(lambda x: ast.literal_eval(x))
xfmr_df["kVAs"] = xfmr_df["kVAs"].apply(lambda x: ast.literal_eval(x))
xfmr_df["taps"] = xfmr_df["taps"].apply(lambda x: ast.literal_eval(x))
xfmr_df["taps"] = xfmr_df["taps"].apply(lambda x: [float(a) for a in x])

xfmr_df["Xscarray"] = xfmr_df["Xscarray"].apply(lambda x: ast.literal_eval(x))
xfmr_df["%Rs"] = xfmr_df["%Rs"].apply(lambda x: ast.literal_eval(x))

linecode_df = pd.DataFrame(data["linecode"])

linecode_df["rmatrix"] = linecode_df["rmatrix"].apply(lambda x: ast.literal_eval(x))
linecode_df["cmatrix"] = linecode_df["cmatrix"].apply(lambda x: ast.literal_eval(x))
linecode_df["xmatrix"] = linecode_df["xmatrix"].apply(lambda x: ast.literal_eval(x))




final_dict = {
    "line": line_df.to_dict(orient="records"),
    "transformer": xfmr_df.to_dict(orient="records"),
    "linecode": linecode_df.to_dict(orient="records")
    
}

on = r"C:\Users\SABRAHAM\Documents\GitHub\Tools\disco\disco\extensions\upgrade_simulation\upgrades\smartds_upgrades_technical_catalog_v1.json"
with open(on, "w") as outfile:
    json.dump(final_dict, outfile, indent=2)


# read output summary and save as csv
import json
import pandas as pd
fp = r"C:\Users\SABRAHAM\Documents\GitHub\Tools\disco\output-debug"
fn = "upgrade_summary.json"
with open(os.path.join(fp, fn), 'r') as f:
    data = json.load(f)

