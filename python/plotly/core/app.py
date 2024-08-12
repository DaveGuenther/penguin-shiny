# Load data and compute static values
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_plotly
from plotnine import ggplot, aes, geom_bar
import plotly.graph_objects as go
import pandas as pd
import palmerpenguins
import itertools
#from plotly.callbacks import Points, InputDeviceState
#points, state = Points(), InputDeviceState()


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
            ui.output_text_verbatim('hover_info_output'),
            ui.output_text_verbatim('click_info_output'),
            ui.output_text_verbatim('selection_info_output'),
            ui.output_text_verbatim("results"),
            ui.tags.script('''
                           $(document).on("keypress", function (e) {
                               Shiny.onInputChange("mydata", e.which);
                               });
                               ''')
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
    
    selection_filter=reactive.value({})
    click_filter=reactive.value({})
    hover_info=reactive.value({})

    def setHoverValues(trace, points, selector):
        if not points.point_inds:
            return
        hover_info.set(points)

    def setClickedValues(trace, points, selector):
        if not points.point_inds:
            return
        click_filter.set({'year':points.xs,input.category():points.trace_name})

    def setSelectedValues(trace, points, selector):
        # Pull existing values of trace filters.  We will replace them with new values
        action_filters=selection_filter.get()
        action_filters=action_filters.copy() # Establish a new location in memory so that it acts like an immutable object

        # This function is called once for every trace (For each possible value of the selected category)
        if not points.point_inds:
            if points.trace_name+'year' in action_filters:
                action_filters.pop(points.trace_name+'year') # If nothing was selected, remove it's filter
        else:
            action_filters[points.trace_name+'year'] = [[points.trace_name], points.xs]
        
        selection_filter.set(action_filters) # Update reactive value with new trace filter

    def figureChanged(fig, figureWidget):
        for trace in fig.data:
            trace.on_hover(setHoverValues)
            trace.on_click(setClickedValues)
            trace.on_selection(setSelectedValues)

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
        # Add additional filters on dataset from segments selected on the visual
        action_filters=selection_filter.get()
        if action_filters:
            #Only run this if chart segments have been selected using the selection tool
            result = [
                (df_filtered_st2['species'].isin(action_filters[key][0]))&  # Species Segment Filter
                (df_filtered_st2['year'].isin(action_filters[key][1]))  # Year Segment Filter
                for key in action_filters.keys() # for ALL traces that registered selections
            ]
            ser_segment_filter = pd.DataFrame(result).any()
            df_filtered_st2 = df_filtered_st2[ser_segment_filter]

        return df_filtered_st2 
    
    @reactive.calc
    def df_summarized():
        return df_filtered_stage1().groupby(['year',input.category()], as_index=False).count().rename({'body_mass_g':"count"},axis=1)[['year',input.category(),'count']]

    @render_widget
    def penguin_plot():
        df_plot = df_summarized()
        bar_columns = list(df_plot['year'].unique()) # x axis column labels
        bar_segments = list(df_plot[input.category()].unique()) # bar segment category labels
        data = [go.Bar(name=segment, x=bar_columns,y=list(df_plot[df_plot[input.category()]==segment]['count'].values), customdata=[input.category()]) for segment in bar_segments]
        fig = go.Figure(data)
        fig.update_layout(barmode="stack")
        fig.layout.xaxis.fixedrange = True
        fig.layout.yaxis.fixedrange = True
        figWidget = go.FigureWidget(fig)
        #selection_filter.set({})
        for trace in figWidget.data:
            trace.on_hover(setHoverValues)
            trace.on_click(setClickedValues)
            trace.on_selection(setSelectedValues)        
        #figureWidget.layout.on_change(figureChanged, figureWidget)


        return figWidget
    
    @render.text
    def hover_info_output():
        return hover_info.get()

    @render.text
    def click_info_output():
        return click_filter.get()

    @render.text
    def selection_info_output():
        return selection_filter.get()

    @render.text
    def total_rows():
        return "Total Rows: "+str(df_filtered_stage2().shape[0])

    @render.table
    def table_view():
        return df_filtered_stage2()
    
    @render.text
    def results():
        return input.mydata()

app = App(app_ui, server)

