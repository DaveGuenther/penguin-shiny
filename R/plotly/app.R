library(shiny)
library(dplyr)
library(bslib)
library(palmerpenguins)
library(ggplot2)
library(DT)
library(plotly)

data(package = 'palmerpenguins')
df_penguins=penguins

# Define UI 
ui <- fluidPage(
  # Application title
  titlePanel("Palmer Penguins Analysis"),  
  sidebarLayout(
    sidebarPanel(
      width=2,
      h3("Filters",align="center"),
      
      # Gender Filter
      checkboxGroupInput(
        "sex_filter",
        label="Gender",
        choices = c("Male"="male","Female"="female"),
        selected = c("male","female")
      ),
      
      # Species Filter
      checkboxGroupInput(
        "species_filter",
        label="Species",
        choices = c("Adelie"="Adelie","Chinstrap"="Chinstrap","Gentoo"="Gentoo"),
        selected = c("Adelie","Chinstrap","Gentoo"),
      ),
      
      # Island Filter
      checkboxGroupInput(
        "island_filter",
        label="Island",
        choices = c("Biscoe"="Biscoe","Dream"="Dream","Torgersen"="Torgersen"),
        selected = c("Biscoe","Dream","Torgersen"),
      ),
      
      
      h3("Parameters", align="center"),
      
      # Category Parameter
      radioButtons(
        "category",
        label="View Penguins by:",
        choices = c("Species"="species", "Island"="island", "Gender"="sex"),
        selected = "species"
        
      ),
    ),
    mainPanel(
      width=10,
      fluidRow(
        # Main Plot
        h3(textOutput("chart_title")),
        plotlyOutput("penguin_plot"),
        verbatimTextOutput("hover"),
      ),
      fluidRow(
        # Count of Visible Rows
        h3(textOutput("total_rows")),
      ),
      fluidRow(
        # Table View
        column(width = 12,
               DT::dataTableOutput("table_view"),style = "height:300px; overflow-y: scroll"
        )
      ),
    ),
    
  ),
)

# Define server logic 
server <- function(input, output) {
  
  category <- reactive({
    # Used to add dynamic category information to the Chart Title
    switch(
      input$category,
      "species"="Species",
      "island"="Island",
      "sex"="Gender"
    )
  })
  
  df_filtered_stage1 <- reactive({
    # Filter based on selections in the filter shelf only (not combining the plot)
    df_penguins %>% 
      filter(species %in% input$species_filter) %>% 
      filter(island %in% input$island_filter) %>%
      filter(sex %in% input$sex_filter)
  })
  
  df_filtered_stage2 <- reactive({
    # Add to filtered_stage1 any additional year/species information captured from clicking on a ber segment
    d <- event_data("plotly_click", source="A") # Get event data for just the main plot (A)
    
    if (is.null(d)){
      # no plot segment is selected, then just show the stage1 (shelf only) filtered dataset
      df_final_filtered <- df_filtered_stage1()
    } else {
      # Some segment was clicked on the bar. Add that selection as a filter to the stage1 dataset
      df_final_filtered <- df_filtered_stage1() %>% filter(.data[[input$category]]==d$customdata) %>% filter(year==d$x)
    }
    df_final_filtered
  })
  
  
  df_summarized <- reactive({
    # Produces summarized view that is very small and intended for plotly chart visualization
    df_filtered_stage1() %>% count(year,.data[[input$category]])
  })
  
  output$hover <- renderPrint({
    # (Optional) Used to help illustrate the event_data object and how it's extended with customdata argument
    event_data("plotly_hover", source="A")
  })
  
  # Dynamic Title
  output$chart_title <- renderText(paste("Number of Palmer Penguins by ",category()," and by Year"))
  
  # Main Plot
  output$penguin_plot <- renderPlotly( 
    plot_ly(df_summarized(), 
            x=~year, 
            y=~n, 
            type='bar', 
            color=~(.data[[input$category]]), 
            source="A", # Used to link the event_data queries to just this plot
            customdata=~(.data[[input$category]])) %>% 
      layout(barmode = 'stack')
  )
  
  # Total Rows
  output$total_rows <- renderText(paste("Total Rows: ", nrow(df_filtered_stage2())))
  
  # Main Table
  output$table_view <- renderDataTable({
    datatable(
      df_filtered_stage2(), 
      options = list(paging = FALSE, dom='t')) # turns off search and paging    
  })
  
}

# Run the application 
shinyApp(ui = ui, server = server)
