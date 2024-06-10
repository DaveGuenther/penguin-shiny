# Load data and compute static values
from shiny import App, reactive, render, ui
from plotnine import ggplot, aes, geom_bar
import palmerpenguins


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
            ui.output_plot('penguin_plot'),
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
    def df_filtered():
        '''This function caches the filtered datframe based on selections in the view'''
        return df_penguins[
            (df_penguins['species'].isin(input.species_filter())) &
            (df_penguins['island'].isin(input.island_filter())) &
            (df_penguins['sex'].isin(input.sex_filter()))]

    @render.plot
    def penguin_plot():
        return (
            ggplot(df_filtered(), aes(x='year', fill=input.category())) 
            + geom_bar()
            )

    @render.text
    def total_rows():
        return "Total Rows: "+str(df_filtered().shape[0])

    @render.table
    def table_view():
        return df_filtered()

app = App(app_ui, server)

