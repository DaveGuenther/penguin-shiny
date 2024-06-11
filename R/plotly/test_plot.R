library(shiny)
library(dplyr)
library(bslib)
library(palmerpenguins)
library(ggplot2)
library(DT)
library(plotly)

data(package = 'palmerpenguins')
df_penguins=penguins

df_summarized <- df_penguins %>% count(year,species)

plot_ly(df_summarized, x=~year, y=~n, type='bar', color=~species) %>% 
  layout(barmode = 'stack')

