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
  
  
  df_filtered <- reactive({
    # Filter based on selections in view 
    df_penguins %>% 
      filter(species %in% input$species_filter) %>% 
      filter(island %in% input$island_filter) %>%
      filter(sex %in% input$sex_filter) ## possibly add plot_click() related filter here?
  })
  
  df_summarized <- reactive({
    df_filtered() %>% count(year,.data[[input$category]])
  })
  
  
  # Dynamic Title
  output$chart_title <- renderText(paste("Number of Palmer Penguins by ",category()," and by Year"))
  
  # Main Plot
  output$penguin_plot <- renderPlotly( 
    plot_ly(df_summarized(), x=~year, y=~n, type='bar', color=~(.data[[input$category]])) %>% 
      layout(barmode = 'stack')
    #ggplot(df_filtered(), aes(x=year, fill=.data[[input$category]])) +
    #  geom_bar()
  )
  
  # Total Rows
  output$total_rows <- renderText(paste("Total Rows: ", nrow(df_filtered())))
  
  # Main Table
  output$table_view <- renderDataTable({
    datatable(
      df_filtered(), 
      options = list(paging = FALSE, dom='t')) # turns off search and paging
  })
  
}

# Run the application 
shinyApp(ui = ui, server = server)
