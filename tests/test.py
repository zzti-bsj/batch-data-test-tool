import ipywidgets as widgets
files_dropdown = widgets.Dropdown(
    options=files,
    value=files[0],
    description='Step001.选择数据文件',
    disabled=False,
)