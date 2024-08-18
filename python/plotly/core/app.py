# Load data and compute static values
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, render_plotly
from plotnine import ggplot, aes, geom_bar
from htmltools import div
import plotly.graph_objects as go
import pandas as pd
import palmerpenguins
import numpy as np
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
            ui.h5("Apparent Issues:"),
        ui.div("1. Selecting individual bar segments on bar chart (",
               ui.a({'href':'https://plotly.com/python-api-reference/generated/plotly.html#plotly.basedatatypes.BaseTraceType.on_click'}, "on_click"),
               ") doesn't allow for an exit-event-like function (such as off_click) when the user double clickes on the white-space of the visual.  Box and Lasso select have (",
               ui.a({'href':'https://plotly.com/python-api-reference/generated/plotly.html#plotly.basedatatypes.BaseTraceType.on_selection'},"on_selection"), 
               ") do this using ",
               ui.a({'href':'https://plotly.com/python-api-reference/generated/plotly.html#plotly.basedatatypes.BaseTraceType.on_deselect'}, "on_deselect"),
               "."),
            output_widget('penguin_plot'),
            ui.span("on_hover Data: "),
            ui.output_text_verbatim('hover_info_output'),
            ui.span("on_click Data: "),
            ui.output_text_verbatim('click_info_output'),
            ui.span("on_selection Data: "),
            ui.output_text_verbatim('selection_info_output'),

            ui.tags.script('''
                            console.log("Initializing!"); 
                            $(document).on("click", function(e){
                                Shiny.onInputChange("ctrlPressed", e.ctrlKey);
                            })
                           '''),
            ui.span("Control Key Pressed:"),
            ui.output_text_verbatim("results"),
        ),
        ui.card( # Table
            ui.card_header(ui.output_text('total_rows')),
            ui.column(
                12, #width
                ui.output_table('table_view'),
                style="height:300px; overflow-y: scroll"
            )
        ),
        ui.a({'href':"https://github.com/DaveGuenther/penguin-shiny/blob/stack-exchange-deselect-hightlight-question/python/plotly/core/app.py"}, "View Source"),
        
    ),
    
)

def server (input, output, session):
    
    selection_filter=reactive.value({})
    click_filter=reactive.value({})
    click_opacity=reactive.value({})
    hover_info=reactive.value({})

    def setHoverValues(trace, points, selector):
        if not points.point_inds:
            return
        hover_info.set(points)

    def highlightBars(figWidget):
        opacity_dict=click_opacity.get()
        
        # First look through all points in all tractes to see if at least one point was selected
        any_points_clicked = False
        if opacity_dict: # initial load will be empty
            any_points_clicked = True in [1 in trace for trace in opacity_dict.values()]
        # if no points were selected, reset opacity to 1 for all points
        if any_points_clicked:
            for trace,opacity_array in zip(figWidget.data,opacity_dict.values()):
                trace.marker.opacity=opacity_array
        else:
            for trace in figWidget.data:
                trace.marker.opacity=1


    def setClickedValues(trace, points, selector):
        inds = np.array(points.point_inds)
        opacity_dict=click_opacity.get().copy()
        opacity_array = np.full(len(trace.x), .2, dtype=float) # create 1d array of opacity values for elements in this trace
        if inds.size: # if any were selected in the trace, set their opacity to 1
            opacity_array[inds] = 1
            #trace.marker.opacity = opacity_array        

        opacity_dict[trace.name]=opacity_array
        click_opacity.set(opacity_dict)
        if not points.point_inds:
            return
    
        click_filter.set({'year':points.xs,input.category():points.trace_name})
    
    def setSelectedValues(trace, points, selector):
        # Pull existing values of trace filters.  We will replace them with new values
        action_filters=selection_filter.get()
        action_filters=action_filters.copy() # Establish a new location in memory so that it acts like an immutable object

        # This function is called once for every trace (For each possible value of the selected category)
        if not points.point_inds:
            if (points.trace_name+'year' in action_filters)&(not input.ctrlPressed()):
                action_filters.pop(points.trace_name+'year') # If nothing was selected and Ctrl wasn't pressed, remove it's filter
        else:
            if ((points.trace_name+'year' in action_filters.keys())&input.ctrlPressed()):
                action_filters[points.trace_name+'year'] = [[points.trace_name], list(set(action_filters[points.trace_name+'year'][1]+points.xs))]
            else:
                action_filters[points.trace_name+'year'] = [[points.trace_name], points.xs]
        
        selection_filter.set(action_filters) # Update reactive value with new trace filter

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


        for trace in figWidget.data:
            trace.on_hover(setHoverValues)
            trace.on_click(setClickedValues)
            trace.on_selection(setSelectedValues) 

        highlightBars(figWidget)

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
        return input.ctrlPressed()

app = App(app_ui, server)

