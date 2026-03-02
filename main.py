# 2026.03.02  18.00
# https://heeki.medium.com/building-an-mcp-server-as-an-api-developer-cfc162d06a83
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastmcp import FastMCP

# ----- 1. Initalize Dash -----
app = dash.Dash(__name__, use_pages=True, suppress_callback_exceptions=True, 
    external_stylesheets=[dbc.themes.DARKLY, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"])

# ----- 2. NOW IMPORT YOUR PAGES -----
from pages import home, bybit,  databricks, air_dataset, lufthansa
import apis.bybit_api as bybit
import apis.kraken_api as kraken
import apis.lufthansa_api as lufthansa
import apis.youtube_api as youtube

# ----- 3. FASTAPI WRAPPER -----
#server = FastAPI(title="Dash Main App")
#server = FastAPI(title="Dash Main App", lifespan=lambda app: youtube.mcp.session_manager.run())
#server = FastAPI(title="Dash Main App",lifespan=youtube.lifespan)
#server.mount("/youtube", youtube.mcp.http_app(stateless_http=True))

youtube_app = youtube.mcp.http_app(stateless_http=True)
server = FastAPI(title="Dash Main App", lifespan=youtube_app.lifespan)
server.mount("/youtube", youtube_app)


# ----- 3.1 HEALTH ENDPOINT -----
@server.get("/health")
def health():
    return {"status": "ok"}

# ----- 3.2. API ROUTERS -----
#server.mount("/youtube", youtube.mcp.sse_app())
#server.mount("/youtube", youtube.mcp.streamable_http_app())
#server.mount("/youtube", youtube.mcp.http_app(stateless_http=True))

server.include_router(bybit.router,         prefix="/api/bybit",         tags=["Bybit"])
server.include_router(kraken.router,        prefix="/api/kraken",        tags=["Kraken"])
server.include_router(databricks.router,    prefix="/api/dbricks",       tags=["Machine Learning"])
server.include_router(air_dataset.router,   prefix="/api/airdata",       tags=["Air Data"])
server.include_router(lufthansa.router,     prefix="/api/lufthansa",     tags=["Lufthansa"])
server.include_router(youtube.router,       prefix="/api/youtube",       tags=["Youtube"])

# ----- 4. Mount Dash to FastAPI -----
server.mount("/", WSGIMiddleware(app.server))

# ----- 5. SIDEBAR & LAYOUT  (Your Modern Layout) -----
SIDEBAR_STYLE = {
    "position": "fixed", "top": "15px", "left": "15px", "bottom": "15px",
    "width": "220px", "padding": "2rem 1rem",
    "background": "rgba(255, 255, 255, 0.1)",
    "backdrop-filter": "blur(15px)",
    "border-radius": "20px",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "box-shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.5)"
}

sidebar = html.Div([
    html.H5("PETROSOFT(EU) CLOUD", className="text-center mb-4", style={"letterSpacing": "2px", "color": "ivory"}),
    
    html.Div([
        html.Div([
            html.I(className="fas fa-user-circle fa-2x text-info"),
            html.Div([
                html.P("Admin Console", className="mb-0", style={"fontSize": "14px", "fontWeight": "bold"}),
                html.P("8GB KVM2", className="text-muted small mb-0")
            ], className="ms-3")
        ], className="d-flex align-items-center p-3", style={"background": "rgba(0,0,0,0.3)", "borderRadius": "15px"})
    ], className="mb-4"),

    html.Hr(style={"color": "rgba(255,255,255,0.3)"}),

    dbc.Nav([
        dbc.NavLink([
            html.Div([
                html.I(className=f"fas {page.get('icon', 'fa-chart-line')} me-2"),
                html.Span(page["name"]),
            ], className="d-flex align-items-center")
        ], href=page["relative_path"], active="exact", className="mb-2 py-2 ps-2 rounded-3 text-light")
        for page in dash.page_registry.values()
    ], vertical=True, pills=True),
], style=SIDEBAR_STYLE)

app.layout = html.Div([
    sidebar,
    html.Div(dash.page_container, style={
        "marginLeft": "250px", "padding": "2rem",
        "background": "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        "minHeight": "100vh"
    })
])
