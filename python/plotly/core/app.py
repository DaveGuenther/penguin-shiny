# Load data and compute static values
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_plotly
from plotnine import ggplot, aes, geom_bar
import plotly.graph_objects as go
import palmerpenguins
from plotly.callbacks import Points, InputDeviceState
points, state = Points(), InputDeviceState()


df_penguins = palmerpenguins.load_penguins()

dict_category = {'species':'Species','island':'Island','sex':'Gender'}

def filter_shelf():
    return ui.card(
        ui.card_header(
            "Filters", 
            align="center",
        ),
        # Gender Filter
        ui.input_checkbox_group(
            'sex_filter', 
            label='Gender', 
            choices={value:(value.capitalize() if (type(value)==str) else value) for value in df_penguins['sex'].unique()},
            selected=list(df_penguins['sex'].unique()),
        ),

        # Species Filter
        ui.input_checkbox_group(
            'species_filter', 
            label='Species', 
            choices=list(df_penguins['species'].unique()),
            selected=list(df_penguins['species'].unique()),
        ),

        # Island Filter
        ui.input_checkbox_group(
            'island_filter', 
            label='Island', 
            choices=list(df_penguins['island'].unique()),
            selected=list(df_penguins['island'].unique()),
        ),
    )

def parameter_shelf():
    return ui.card(
        ui.card_header(
            'Parameters',
            align='center',
        ),

        # Category Selector
        ui.input_radio_buttons(
            'category', 
            label = 'View Penguins by:', 
            choices=dict_category,
            selected = 'species',
        ),
    ),

app_ui = ui.page_fluid(
    ui.h1("Palmer Penguins Analysis"),
    ui.layout_sidebar(
        # Left Sidebar
        ui.sidebar(
            filter_shelf(),
            parameter_shelf(),
            width=250,
        ),
        
        # Main Panel
        ui.card( # Plot
            ui.card_header(ui.output_text('chart_title')),
            output_widget('penguin_plot'),
        ),
        ui.card( # Table
            ui.card_header(ui.output_text('total_rows')),
            ui.column(
                12, #width
                ui.output_table('table_view'),
                style="height:300px; overflow-y: scroll"
            )
        )
    ),
)

def server (input, output, session):
    
    @reactive.calc
    def category():
        '''This function caches the appropriate Capitalized form of the selected category'''
        return dict_category[input.category()]

    # Dynamic Chart Title
    @render.text
    def chart_title():
        return "Number of Palmer Penguins by Year, colored by "+category()


    @reactive.calc
    def df_filtered_stage1():
        '''This function caches the filtered datframe based on selections in the view'''
        return df_penguins[
            (df_penguins['species'].isin(input.species_filter())) &
            (df_penguins['island'].isin(input.island_filter())) &
            (df_penguins['sex'].isin(input.sex_filter()))]

    @reactive.calc
    def df_filtered_stage2():
        df_filtered_st2 = df_filtered_stage1() 
        # Eventually add additional filters on dataset from segments selected on the visual
        return df_filtered_st2 
    
    @reactive.calc
    def df_summarized():
        return df_filtered_stage2().groupby(['year',input.category()], as_index=False).count().rename({'body_mass_g':"count"},axis=1)[['year',input.category(),'count']]

    @reactive.calc
    def filter_fn():
        print("Clicked!") # This never gets called
        
    @render_widget
    def penguin_plot():
        df_plot = df_summarized()
        bar_columns = list(df_plot['year'].unique()) # x axis column labels
        bar_segments = list(df_plot[input.category()].unique()) # bar segment category labels
        data = [go.Bar(name=segment, x=bar_columns,y=list(df_plot[df_plot[input.category()]==segment]['count'].values), customdata=[input.category()], customdatasrc='A') for segment in bar_segments]
        fig = go.Figure(data)
        fig.update_layout(barmode="stack")
        fig = go.FigureWidget(fig)
        session
        fig.data[0].on_click(
            filter_fn
            )
        return fig
    
    @render.text
    def total_rows():
        return "Total Rows: "+str(df_filtered_stage1().shape[0])

    @render.table
    def table_view():
        df_this=df_summarized()
        return df_filtered_stage1()

app = App(app_ui, server)

