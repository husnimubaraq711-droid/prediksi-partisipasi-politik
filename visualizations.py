"""
Modul yang bertanggung jawab untuk membuat grafik dan visualisasi data 
menggunakan library Plotly (seperti bar chart, line chart, peta choropleth, dll).
"""
import pandas as pd
import plotly.express as px

from src.config import AREA_COLUMN, DISPLAY_NAMES, FEATURE_COLUMNS, TARGET_COLUMN, YEAR_COLUMN


def participation_by_area(df: pd.DataFrame):
    chart_data = (
        df.groupby(AREA_COLUMN, as_index=False)[TARGET_COLUMN]
        .mean()
        .sort_values(TARGET_COLUMN, ascending=False)
    )
    fig = px.bar(
        chart_data,
        x=AREA_COLUMN,
        y=TARGET_COLUMN,
        text=TARGET_COLUMN,
        labels=DISPLAY_NAMES,
        title="Rata-rata Partisipasi Politik per Kecamatan",
        template="plotly_white",
        color_discrete_sequence=["#2563EB"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_ticksuffix="%", xaxis_title="", yaxis_title="Partisipasi Politik")
    return fig


def participation_trend(df: pd.DataFrame):
    chart_data = df.sort_values([AREA_COLUMN, YEAR_COLUMN])
    fig = px.line(
        chart_data,
        x=YEAR_COLUMN,
        y=TARGET_COLUMN,
        color=AREA_COLUMN,
        markers=True,
        labels=DISPLAY_NAMES,
        title="Tren Partisipasi Politik per Tahun",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(yaxis_ticksuffix="%", xaxis_title="Tahun", yaxis_title="Partisipasi Politik")
    return fig


def correlation_heatmap(df: pd.DataFrame):
    corr_cols = [*FEATURE_COLUMNS, TARGET_COLUMN]
    corr = df[corr_cols].corr(numeric_only=True)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        title="Korelasi Antar Variabel",
        labels={"color": "Korelasi"},
        template="plotly_white",
        color_continuous_scale="Blues",
    )
    return fig


def feature_importance_bar(importance_df: pd.DataFrame):
    # Filter out variables with zero importance (constant variables in database)
    filtered_df = importance_df[importance_df["importance"] > 0.0001].copy()
    if filtered_df.empty:
        filtered_df = importance_df
        
    fig = px.bar(
        filtered_df,
        x="importance",
        y="variabel",
        orientation="h",
        text="importance",
        title="Feature Importance Random Forest",
        template="plotly_white",
        color_discrete_sequence=["#2563EB"],
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Importance", yaxis_title="")
    return fig


def prediction_scatter(prediction_df: pd.DataFrame):
    fig = px.scatter(
        prediction_df,
        x="aktual",
        y="prediksi",
        size=prediction_df["selisih"].abs() + 1,
        title="Perbandingan Nilai Aktual vs Prediksi",
        labels={"aktual": "Aktual", "prediksi": "Prediksi"},
        template="plotly_white",
        color_discrete_sequence=["#2563EB"],
    )
    min_value = min(prediction_df["aktual"].min(), prediction_df["prediksi"].min())
    max_value = max(prediction_df["aktual"].max(), prediction_df["prediksi"].max())
    fig.add_shape(
        type="line",
        x0=min_value,
        y0=min_value,
        x1=max_value,
        y1=max_value,
        line={"dash": "dash", "color": "#64748B"},
    )
    return fig


def participation_map(df: pd.DataFrame, geojson: dict, selected_year: int):
    # Filter by selected year
    map_data = df[df[YEAR_COLUMN] == selected_year].copy()
    if map_data.empty:
        map_data = df.copy()
        
    # Group TPS level data into kecamatan level averages for the map
    map_data = map_data.groupby(AREA_COLUMN, as_index=False)[TARGET_COLUMN].mean()
    
    # Convert uppercase kecamatan name (e.g. 'BANJARMASIN TIMUR') to Title Case (e.g. 'Banjarmasin Timur') to match GeoJSON properties.WADMKC
    map_data[AREA_COLUMN] = map_data[AREA_COLUMN].astype(str).str.title()

    fig = px.choropleth_mapbox(
        map_data,
        geojson=geojson,
        locations=AREA_COLUMN,
        featureidkey="properties.WADMKC",
        color=TARGET_COLUMN,
        hover_name=AREA_COLUMN,
        hover_data={TARGET_COLUMN: ":.2f"},
        center={"lat": -3.335, "lon": 114.59},
        zoom=10.5,
        mapbox_style="carto-positron",
        opacity=0.65,
        labels=DISPLAY_NAMES,
        title=f"Peta Partisipasi Politik Tahun {selected_year}",
    )
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig


def participation_comparison_chart(comp_df: pd.DataFrame):
    """Draws a grouped bar chart comparing 2019 vs 2024 participation rates."""
    if comp_df.empty:
        return px.scatter(title="Data Perbandingan Tidak Tersedia")
        
    # Melt dataframe for easy plotting with px.bar
    melted = comp_df.melt(
        id_vars=["kecamatan"],
        value_vars=["partisipasi_2019", "partisipasi_2024"],
        var_name="Tahun",
        value_name="Partisipasi"
    )
    melted["Tahun"] = melted["Tahun"].map({
        "partisipasi_2019": "2019 (Agregat)",
        "partisipasi_2024": "2024 (TPS Agg)"
    })
    
    fig = px.bar(
        melted,
        x="kecamatan",
        y="Partisipasi",
        color="Tahun",
        barmode="group",
        text="Partisipasi",
        title="Perbandingan Partisipasi Politik Per Kecamatan (2019 vs 2024)",
        template="plotly_white",
        color_discrete_map={
            "2019 (Agregat)": "#94A3B8", # Slate/Gray
            "2024 (TPS Agg)": "#ff7f66"   # Coral
        }
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_ticksuffix="%", xaxis_title="", yaxis_title="Partisipasi Politik (%)")
    return fig


def dynamic_participation_comparison_chart(comp_df: pd.DataFrame, y1: int, y2: int):
    """Draws a grouped bar chart comparing any two years' participation rates."""
    import plotly.express as px
    if comp_df.empty:
        return px.scatter(title="Data Perbandingan Tidak Tersedia")
        
    col_y1 = f"partisipasi_{y1}"
    col_y2 = f"partisipasi_{y2}"
    
    # Melt dataframe for easy plotting with px.bar
    melted = comp_df.melt(
        id_vars=["kecamatan"],
        value_vars=[col_y1, col_y2],
        var_name="Tahun",
        value_name="Partisipasi"
    )
    melted["Tahun"] = melted["Tahun"].map({
        col_y1: f"{y1} (Agg)",
        col_y2: f"{y2} (Agg)"
    })
    
    fig = px.bar(
        melted,
        x="kecamatan",
        y="Partisipasi",
        color="Tahun",
        barmode="group",
        text="Partisipasi",
        title=f"Perbandingan Rata-rata Partisipasi Politik Per Kecamatan ({y1} vs {y2})",
        template="plotly_white",
        color_discrete_map={
            f"{y1} (Agg)": "#94A3B8", # Slate/Gray
            f"{y2} (Agg)": "#ff7f66"   # Coral
        }
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_ticksuffix="%", xaxis_title="", yaxis_title="Partisipasi Politik (%)")
    return fig
