import calendar, datetime
from calendar import c, month_name
from distutils.command.upload import upload
from queue import Empty
#from tkinter import PAGES
import streamlit as st
import pandas as pd
import numpy as np
import pandasql as psql
import os
import sys
import time
from tabula import read_pdf, convert_into
#df = read_pdf('')

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/CGI_logo.svg/1200px-CGI_logo.svg.png")
st.header('Time Sheet Review Tool')
st.markdown(""" Welcome!! This tool is used to analyze the timesheet details and provide insights about the SOW """)

uploaded_file = st.file_uploader('Upload the excel file:', accept_multiple_files=False)
if uploaded_file is not None:
    time_data = pd.read_excel(uploaded_file)
    time_data.columns = [c.replace(' ','_') for c in time_data.columns]
    st.markdown('---')

    #Defining the options for radio button on sidebar
    list1 = ['Hours Consumed from SOW', 'Remaining Hours per Role', 'Hours per An_Type per Day', 
    'Hours>8 for any Day', 'Hours>40 per week']
    options = st.sidebar.radio('Options', list1)

    #Setting SOW hours for six months to default 1000
    total_sow_hours = 1000
    
    #Hours entered by individual project members
    df1 = psql.sqldf("""SELECT td2.Project, td2.Name, td2.Hours_Consumed FROM(
                        SELECT td.Project as Project, td.Name as Name, SUM(td.Quantity) as Hours_Consumed
                        FROM time_data td GROUP BY td.Project, td.Name
                    ) AS td2
                    ORDER BY td2.Project, td2.Name
                    """)
    
    def hours_consumed():
        if( len(df1) > 0):
            select_project = st.selectbox("Select Project", psql.sqldf("""SELECT DISTINCT td.Project FROM time_data td"""), key = 'select_project')
            st.subheader('Total hours by project members')
            st.table(df1[(df1["Project"] == select_project)])
            st.markdown('---')
        else:
            st.write('No Records Found')
    

    #Calculating remaining hours from SOW 
    df2 = psql.sqldf("""
                    SELECT td2.Project, td2.Activity, td2.Hours_Consumed FROM(
                        SELECT td.Project as Project, td.Activity as Activity, SUM(td.Quantity) as Hours_Consumed
                        FROM time_data td GROUP BY td.Project, td.Activity
                    ) AS td2
                    ORDER BY td2.Project, td2.Activity
                    """)
    df2.insert(2, 'Total_SOW_Hours', total_sow_hours, True)
    df2['Pending_Hours'] = df2['Total_SOW_Hours'] - df2['Hours_Consumed']

    df7 = psql.sqldf("""SELECT DISTINCT td.Project as Project, td.Activity as Activity FROM time_data td
                                GROUP BY td.Project, td.Activity""")
    

    def fun1():
        st.write(st.session_state.select_project1)

    def remaining_hours_per_role():    
        if( len(df2) > 0):
            #st.subheader('Remaining hours per Role (Activity)')
            left_column, right_column = st.columns(2)
            with left_column:
                select_project = st.selectbox("Select Project", psql.sqldf(""" SELECT DISTINCT td.Project FROM time_data td"""), key = 'select_project1')
            with right_column:
                st.subheader(f'Total SOW hours: {total_sow_hours}')
            if( len(df7) > 0):
                df8 = df7[df7['Project'] == select_project]
                #st.session_state
                st.write("Total Roles(Activities) under selected project: ", len(df8))
                st.write('List of Roles(Activities) under selected project: ', df8)
                st.text('')
                #st.write('df8_project_activity:', df8['Activity'])
                list_of_roles = df8.values.tolist()
                #st.write('list_of_roles: ', list_of_roles)
                df7.insert(2, 'Total_SOW_Hours', total_sow_hours, True)
                df7['Hours_Consumed'] = df2['Hours_Consumed']
                df7['Pending_Hours'] = df2['Pending_Hours']
                st.subheader('Remaining Hours Per Role (Activity):')
                st.table(df7[(df7['Project'] == select_project)])
                df7.insert(5, 'Price_Per_Hour (in $)', 1, True)
                df7.insert(6, 'Remaining_Budget (in $)', 1, True)

                st.subheader('Enter Price Per Hour For Selected Role (Activity) To Get Budget Information:')                
                for i in range(len(df8)):
                    st.write('Selected Role: ', list_of_roles[i][1])
                    price_per_hour = st.number_input('Enter price per hour for selected role:', key = list_of_roles[i], on_change = fun1)
                    #st.session_state
                    if price_per_hour <= 0.00:
                        st.info('Enter valid price i.e. >0.00 ', icon="ℹ️")
                        st.text('')
                    else:
                        st.write('Price entered:', price_per_hour)
                        j = df7[df7['Project'] == select_project].index.tolist()
                        #st.write('Value of i after:', i)
                        st.text('')
                        #st.write('df7 index[i] i.e. j after:', j[i])
                        #st.text('')
                        #st.write('df7 index: ', j)
                        #st.write('df7 index[0] i.e. k:', j[0])
                        k = j[0]
                        l = j[i]
                        #st.write('Value of k: ', k)
                        #st.write('Value of l: ', l)
                        if ((i != k) & (k != 0)):
                            df7['Price_Per_Hour (in $)'][l] = df7['Price_Per_Hour (in $)'][l] * price_per_hour
                            df7['Remaining_Budget (in $)'][l] = df7['Pending_Hours'][l] * df7['Price_Per_Hour (in $)'][l]
                        else:
                            df7['Price_Per_Hour (in $)'][i] = df7['Price_Per_Hour (in $)'][i] * price_per_hour
                            df7['Remaining_Budget (in $)'][i] = df7['Pending_Hours'][i] * df7['Price_Per_Hour (in $)'][i]
                #st.table(df7)
                df7_with_selected_project = df7[(df7['Project'] == select_project)]
                st.table(df7_with_selected_project)
                #st.table(df7_with_selected_project.style.format({"Price_Per_Hour": "{:.2f}"}))
            st.markdown('---')
        else:
            st.write('No Records Found') 
    

    #Calculating Hours per An_Type per Day
    df3 = psql.sqldf("""
                    SELECT td2.Project, td2.Name, td2.Trans_Date, td2.An_Type, td2.Day_Total FROM(
                        SELECT td.Project as Project, td.Name as Name, td.Trans_Date as Trans_Date, td.An_Type as An_Type, SUM(td.Quantity) as Day_Total
                        FROM time_data td GROUP BY td.Project, td.Name, td.Trans_Date, td.An_Type ) AS td2
                        ORDER BY td2.Project, td2.Name, td2.Trans_Date
                    """ )
    def hours_per_An_Type():
        if( len(df3) > 0):
            st.subheader('Individuals with project hours based on An_Type')
            left_column, right_column = st.columns(2)
            with left_column:
                add_radiobutton = st.radio('Select An_Type', psql.sqldf(""" SELECT DISTINCT td.An_Type FROM time_data td"""), key = 'radio_option')
                #st.session_state.radio_option
            with right_column:
                #add_selectbox = st.selectbox('Select the project member', psql.sqldf(""" SELECT DISTINCT td.Name FROM time_data td"""), key = 'select_option')
                add_selectbox = st.selectbox('Select the project', psql.sqldf(""" SELECT DISTINCT td.Project FROM time_data td"""), key = 'select_option')
            if add_radiobutton == 'BIL':
                df4 = df3[(df3.An_Type == 'BIL')]
                #st.table(df4[(df4['Name'] == add_selectbox)])
                st.table(df4[(df4['Project'] == add_selectbox)])
                #st.table(df4)
            elif add_radiobutton == 'CST':
                df4 = df3[(df3.An_Type == 'CST')]
                #st.table(df4[(df4['Name'] == add_selectbox)])
                #st.table(df4)
                st.table(df4[(df4['Project'] == add_selectbox)])
            elif add_radiobutton == 'SHR':
                df4 = df3[(df3.An_Type == 'SHR')]
                #st.table(df4[(df4['Name'] == add_selectbox)])
                #st.table(df4)
                st.table(df4[(df4['Project'] == add_selectbox)])
            elif add_radiobutton == 'CSC':
                df4 = df3[(df3.An_Type == 'CSC')]
                #st.table(df4[(df4['Name'] == add_selectbox)])
                #st.table(df4)
                st.table(df4[(df4['Project'] == add_selectbox)])
            elif add_radiobutton == 'TLX':
                df4 = df3[(df3.An_Type == 'TLX')]
                #st.table(df4[(df4['Name'] == add_selectbox)])
                #st.table(df4)
                st.table(df4[(df4['Project'] == add_selectbox)])
            else:
                st.write('Invalid Option')
            st.markdown('---')
        else:
            st.write('No Records Found')

    
    #Finding individuals with project hours greater than 8 on any Day for particular An_Type
    df14 = psql.sqldf(""" SELECT td2.Project, td2.Name, td2.Trans_Date, td2.An_Type, td2.Day_Total FROM(
                        SELECT td.Project as Project, td.Name as Name, td.Trans_Date as Trans_Date, td.An_Type as An_Type, 
                        SUM(td.Quantity) as Day_Total FROM time_data td 
                        GROUP BY td.Project, td.Name, td.Trans_Date, td.An_Type ) AS td2
                        WHERE td2.Day_Total > 8
                        ORDER BY td2.Project, td2.Name, td2.Trans_Date """)
    #st.table(df14)
    
    def display_CGI_Statutory_Holidays(df10):
        df10 = df10
        if df10 is not None:
            df11 = read_pdf(df10, stream=True, pages = 1)
            df12 = read_pdf(df10, stream=True, pages = 2)
            
           #st.table(df12[0])
            len1 = len(df11[0])
            len2 = len(df12[0])
            len3 = len(df12[1])
            #st.write('length of df11[0]', len1)
            #st.write('length of df12[0]', len2)
            #st.write('length of df12[0]', len3)
            
            var1 = 'Statutory Holiday'
            var2 = 'Date'
            var3 = 'Unnamed: 0'

            if ((len1 > 0) & (var1 in df11[0].columns)):
                #st.write('hi df11[0]...')
                if ((var2 in df11[0].columns) & (var3 in df11[0].columns)):
                    df11[0][var2] = df11[0][var3]
                    df11[0] = df11[0].drop(var3, axis=1)
                    #st.table(df11[0])
                #else:
                    #st.table(df11[0])
            if ((len2 > 0) & (var1 in df12[0].columns)):
                #st.write('hi df12[0] with Statutory', df12[0].columns)
                if ((var2 in df12[0].columns) & (var3 in df12[0].columns)):
                    df12[0][var2] = df12[0][var3]
                    df12[0] = df12[0].drop(var3, axis=1)
                    #st.table(df12[0])
                    st.text('')
                #else:
                    #st.table(df12[0])
                    #st.text('')
            elif ((len2 > 0) & (var1 not in df12[0].columns)):
                #st.write('hi df12[0] without Statutory', df12[0].columns)
                df13 = df12[0].columns.to_frame().T.append(df12[0], ignore_index=True)
                df13.columns = range(len(df13.columns))
                #st.table(df13)
                st.text('')
            if ((len3 > 0) & (var1 in df12[1].columns)):
                #st.write('df12[1]', df12[1].columns)
                if ((var2 in df12[1].columns) & (var3 in df12[1].columns)):
                    df12[1][var2] = df12[1][var3]
                    df12[1] = df12[1].drop(var3, axis=1)
                    #st.table(df12[1])
                #else:
                    #st.table(df12[1])

            list1 = df11[0].values.tolist()
            #st.write('list1', list1)
            list2 = df13.values.tolist()
            #st.write('list2', list2)
            list3 = df12[1].values.tolist()
            #st.write('list3', list3)
            list_of_holidays = list1+(list2)+(list3)
            #st.write('list_of_holidays', list_of_holidays)
            return list_of_holidays
        else:
            st.info('Upload CGI Statutory Holidays PDF file to proceed.', icon="ℹ️")
            return False

    def hours_greater_than_8_for_An_Type_for_any_day():
        st.subheader('Upload CGI Statutory Holidays PDF file to proceed')
        df10 = st.file_uploader('Upload CGI Statutory Holidays PDF File:', accept_multiple_files=False)
        if df10 is not None:
            list_of_holidays = display_CGI_Statutory_Holidays(df10)
            if (list_of_holidays != False):
                if( len(df14) > 0):
                    len1 = len(list_of_holidays)
                    st.write('Total holidays given in uploaded pdf file', len1)
                    st.text('')
                    st.text('')
                    
                    list_of_holidays = pd.DataFrame(list_of_holidays).dropna()
                    list_of_holidays = list_of_holidays.reset_index()
                    #st.write('New list_of_holidays', list_of_holidays)
                    len_new = len(list_of_holidays)
                    #st.write('Total holidays after removing bad records', len_new)
                    #st.write('iloc0', list_of_holidays.iloc[0])
                    #st.write('iloc1', list_of_holidays.iloc[1])
                    #st.write('iloc01', list_of_holidays.iloc[0][1])
                    #st.write('iloc01:18', list_of_holidays.iloc[0][1][:18])
                    
                    list_of_holidays[1] = list_of_holidays[1].str.replace('observed', '')
                    list_of_holidays[1] = list_of_holidays[1].str.replace('(', '')
                    list_of_holidays[1] = list_of_holidays[1].str.replace(')', '')
                    list_of_holidays[1] = list_of_holidays[1].str.strip()
                    #st.write('listllll:', list_of_holidays)
                    #st.write('list_of_holidays[1]:', list_of_holidays[1])
                    #st.write('list_of_holidays[1]:', list_of_holidays[1][0])
                    #st.write('list_of_holidays[1]:', list_of_holidays[1][1])
                    
                    for i in range(len_new):
                        #st.write("Value of i:", i)
                        #st.write('list_of_holidays[1][i]', list_of_holidays[1][i])
                        if len(list_of_holidays[1][i]) > 18:
                            #st.write('iloc0', list_of_holidays.iloc[i])
                            #st.write('iloc01', list_of_holidays.iloc[i][1])
                            #st.write('iloc01[:18]', list_of_holidays.iloc[i][1][:18])
                            #st.write('list_of_holidays[1][i]', list_of_holidays[1][i])
                            list_of_holidays[1][i] = list_of_holidays.iloc[i][1][:18]
                            #st.write('list_of_holidays[i]:', list_of_holidays[1][i])
                    #st.write('New list_of_holidays after for loop', list_of_holidays)
                    list_of_holidays['Statutory Holiday'] = list_of_holidays[0]
                    list_of_holidays = list_of_holidays.drop(0, axis=1)
                    list_of_holidays['Cleaned_Dates'] = list_of_holidays[1]
                    list_of_holidays = list_of_holidays.drop(1, axis=1)

                    st.write('CGI Holiday List after cleaning data', list_of_holidays)
                    #st.write('List of cols:', list_of_holidays.columns)
                    
                    st.subheader('Individuals with project hours greater than 8 on any Day for particular An_Type')
                    st.warning('**Individuals found with project hours greater than 8 on any Day for particular An_Type', icon="⚠️")

                    left_column, right_column = st.columns(2)
                    with left_column:
                        add_radiobutton = st.radio('Select An_Type', psql.sqldf(""" SELECT DISTINCT td.An_Type FROM time_data td""" ), key = 'radio_option1')
                    with right_column:
                        add_selectbox = st.selectbox('Select the project', psql.sqldf(""" SELECT DISTINCT td.Project FROM time_data td"""), key = 'select_option1')
                    if add_radiobutton == 'BIL':
                        df15 = df14[(df14.An_Type == 'BIL')]
                        df16 = pd.to_datetime(df15['Trans_Date'], format = '%Y/%m/%d')
                        month = df16.dt.month_name().astype(str)
                        day_from_df16 = df16.dt.day.astype(str)
                        year = df16.dt.year.astype(str)
                        converted_date = month + ' ' + day_from_df16 + ', ' + year
                        df15['Converted_Trans_Date'] = converted_date
                        #st.write('df15', df15)
                        if len(df15) > 0:   
                            index_of_df15 = df15.index.tolist()
                            #st.write('Index of df15', index_of_df15)
                            index_of_first_element_of_list = index_of_df15[0]
                            #st.write('Index[0] of df15', index_of_first_element_of_list)
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15])
                            j = len(df15)
                            #st.write('Length of df15', j)
                            df15['CGI_Statutory_Holiday'] = ''        
                            a = list_of_holidays['Cleaned_Dates'].values.tolist()
                            #st.write('Value of a', a)
                            len_of_a = len(a)
                            #st.write('Length of a', len_of_a)
                            #st.write('a:len_of_a', a[:len_of_a])
                            for k in range(j):
                                if index_of_first_element_of_list == 0:
                                    if ((df15['Converted_Trans_Date'][k] in a[:len_of_a])):
                                        #st.write('Hello when first_element_of_list == 0 and df15[Converted_Trans_Date][k] in a[:len_of_a]')
                                        #st.write('index_of_first_element_of_list', index_of_first_element_of_list)
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        df15['CGI_Statutory_Holiday'][k] = 'CGI Holiday'
                                    else:
                                        #st.write('Else block when first_element_of_list == 0 BUT df15[Converted_Trans_Date][k] NOT IN a[:len_of_a]')
                                        #st.write('index_of_first_element_of_list', index_of_first_element_of_list)
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        df15['CGI_Statutory_Holiday'][k] = 'No CGI Holiday'
                                else:
                                    if ((df15['Converted_Trans_Date'][index_of_first_element_of_list] in a[:len_of_a])):
                                        #st.write('Hello when first_element_of_list != 0 and df15[Converted_Trans_Date][] in a[:len_of_a]')
                                        #st.write('first_element_of_list', index_of_first_element_of_list)
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][index_of_first_element_of_list])
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('New value of first_element_of_list', index_of_first_element_of_list)
                                    else:
                                        #st.write('Else block when first_element_of_list != 0 BUT df15[Converted_Trans_Date][] NOT IN a[:len_of_a]')
                                        #st.write('index_of_first_element_of_list', index_of_first_element_of_list)
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'No CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('New Value of first_element_of_list in Else Block', index_of_first_element_of_list)          
                        st.table(df15[(df15['Project'] == add_selectbox)])
                    elif add_radiobutton == 'CST':
                        df15 = df14[(df14.An_Type == 'CST')]
                        df16 = pd.to_datetime(df15['Trans_Date'], format = '%Y/%m/%d')
                        month = df16.dt.month_name().astype(str)
                        day_from_df16 = df16.dt.day.astype(str)
                        year = df16.dt.year.astype(str)
                        converted_date = month + ' ' + day_from_df16 + ', ' + year
                        df15['Converted_Trans_Date'] = converted_date
                        #st.write('df15', df15)
                        if len(df15) > 0:
                            index_of_df15 = df15.index.tolist()
                            #st.write('Index of df15', index_of_df15)
                            index_of_first_element_of_list = index_of_df15[0]
                            #st.write('Index[0] of df15', first_element_of_list)
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15])
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15][0])
                            j = len(df15)
                            #st.write('Length of df15', j)
                            df15['CGI_Statutory_Holiday'] = ''        
                            a = list_of_holidays['Cleaned_Dates'].values.tolist()
                            #st.write('Value of a', a)
                            len_of_a = len(a)
                            #st.write('Length of a', len_of_a)
                            for k in range(j):
                                if index_of_first_element_of_list == 0:
                                    if ((df15['Converted_Trans_Date'][k] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][k] = 'CGI Holiday'
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][k] = 'No CGI Holiday'
                                else:
                                    if ((df15['Converted_Trans_Date'][index_of_first_element_of_list] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'No CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                        st.table(df15[(df15['Project'] == add_selectbox)])
                    elif add_radiobutton == 'SHR':
                        df15 = df14[(df14.An_Type == 'SHR')]
                        df16 = pd.to_datetime(df15['Trans_Date'], format = '%Y/%m/%d')
                        month = df16.dt.month_name().astype(str)
                        day_from_df16 = df16.dt.day.astype(str)
                        year = df16.dt.year.astype(str)
                        converted_date = month + ' ' + day_from_df16 + ', ' + year
                        df15['Converted_Trans_Date'] = converted_date
                        #st.write('df15', df15)
                        if len(df15) > 0:
                            index_of_df15 = df15.index.tolist()
                            #st.write('Index of df15', index_of_df15)
                            index_of_first_element_of_list = index_of_df15[0]
                            #st.write('Index[0] of df15', first_element_of_list)
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15])
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15][0])
                            j = len(df15)
                            #st.write('Length of df15', j)
                            df15['CGI_Statutory_Holiday'] = ''        
                            a = list_of_holidays['Cleaned_Dates'].values.tolist()
                            #st.write('Value of a', a)
                            len_of_a = len(a)
                            #st.write('Length of a', len_of_a)
                            for k in range(j):
                                if index_of_first_element_of_list == 0:
                                    if ((df15['Converted_Trans_Date'][k] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][k] = 'CGI Holiday'
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][k] = 'No CGI Holiday'
                                else:
                                    if ((df15['Converted_Trans_Date'][index_of_first_element_of_list] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'No CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                        st.table(df15[(df15['Project'] == add_selectbox)])
                    elif add_radiobutton == 'CSC':
                        df15 = df14[(df14.An_Type == 'CSC')]
                        #st.table(df5)
                        df16 = pd.to_datetime(df15['Trans_Date'], format = '%Y/%m/%d')
                        month = df16.dt.month_name().astype(str)
                        day_from_df16 = df16.dt.day.astype(str)
                        year = df16.dt.year.astype(str)
                        converted_date = month + ' ' + day_from_df16 + ', ' + year
                        df15['Converted_Trans_Date'] = converted_date
                        #st.write('df15', df15)
                        if len(df15) > 0:
                            index_of_df15 = df15.index.tolist()
                            #st.write('Index of df15', index_of_df15)
                            index_of_first_element_of_list = index_of_df15[0]
                            #st.write('Index[0] of df15', first_element_of_list)
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15])
                            j = len(df15)
                            #st.write('Length of df15', j)
                            df15['CGI_Statutory_Holiday'] = ''        
                            a = list_of_holidays['Cleaned_Dates'].values.tolist()
                            #st.write('Value of a', a)
                            len_of_a = len(a)
                            #st.write('Length of a', len_of_a)
                            for k in range(j):
                                if index_of_first_element_of_list == 0:
                                    if ((df15['Converted_Trans_Date'][k] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][k] = 'CGI Holiday'
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][k] = 'No CGI Holiday'
                                else:
                                    if ((df15['Converted_Trans_Date'][index_of_first_element_of_list] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Hello')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Else block')
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'No CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('Value of first_element_of_list', first_element_of_list)
                        st.table(df15[(df15['Project'] == add_selectbox)])
                    elif add_radiobutton == 'TLX':
                        df15 = df14[(df14.An_Type == 'TLX')]
                        #st.table(df15)
                        df16 = pd.to_datetime(df15['Trans_Date'], format = '%Y/%m/%d')
                        month = df16.dt.month_name().astype(str)
                        #st.write('Month name', month)
                        day_from_df16 = df16.dt.day.astype(str)
                        year = df16.dt.year.astype(str)
                        #st.write('Year#', year)
                        converted_date = month + ' ' + day_from_df16 + ', ' + year
                        #st.write('Converted Date:', converted_date)
                        df15['Converted_Trans_Date'] = converted_date
                        #st.write('df15', df15)
                        if len(df15) > 0:
                            index_of_df15 = df15.index.tolist()
                            #st.write('Index of df15', index_of_df15)
                            index_of_first_element_of_list = index_of_df15[0]
                            #st.write('First element of list i.e. index starting from', first_element_of_list)
                            #st.write('df15_Converted_Date', df15['Converted_Trans_Date'][index_of_df15])
                            j = len(df15)
                            #st.write('Length of df15', j)
                            df15['CGI_Statutory_Holiday'] = ''        
                            a = list_of_holidays['Cleaned_Dates'].values.tolist()
                            #st.write('Value of a', a)
                            len_of_a = len(a)
                            #st.write('Length of a', len_of_a)
                            for k in range(j):
                                if index_of_first_element_of_list == 0:
                                    if ((df15['Converted_Trans_Date'][k] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Hello!! First element of list is 0')
                                        df15['CGI_Statutory_Holiday'][k] = 'CGI Holiday'
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][k])
                                        #st.write('Else block when first element of list is 0')
                                        df15['CGI_Statutory_Holiday'][k] = 'No CGI Holiday'
                                else:
                                    if ((df15['Converted_Trans_Date'][index_of_first_element_of_list] in a[:len_of_a])):
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Hello when index_of_first_element_of_list !=0 and value is in holiday list')
                                        #st.write('index_of_first_element_of_list', index_of_first_element_of_list)
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('New value of index_of_first_element_of_list', index_of_first_element_of_list)
                                    else:
                                        #st.write('df15[k]', df15['Converted_Trans_Date'][first_element_of_list])
                                        #st.write('Else block when index_of_first_element_of_list !=0 BUT value is NOT IN holiday list')
                                        #st.write('index_of_first_element_of_list', index_of_first_element_of_list)
                                        df15['CGI_Statutory_Holiday'][index_of_first_element_of_list] = 'No CGI Holiday'
                                        index_of_first_element_of_list += 1
                                        #st.write('New value of index_of_first_element_of_list', index_of_first_element_of_list)
                        st.table(df15[(df15['Project'] == add_selectbox)])
                    else:
                        st.write('Invalid Option')
                        st.markdown('---')
                else:
                    st.write('Great!! Nobody found with hours greater than 8 on any Day for particular An_Type. :smile:')
            
            

    #Check if any individual entered hours > 40 for any week
    df6 = psql.sqldf(""" SELECT td2.Project, td2.Name, td2.Acctg_Date, td2.An_Type, td2.total_hours FROM(
                                    SELECT td.Project as Project, td.Name as Name, td.Acctg_Date as Acctg_Date, 
                                    td.An_Type as An_Type, SUM(td.Quantity) as total_hours
                                    FROM time_data td GROUP BY td.Project, td.Name, td.Acctg_Date, td.An_Type
                                ) AS td2
                                WHERE td2.total_hours > 40
                                ORDER BY td2.Name 
                                """)
    def hours_greater_than_40_any_week():
        if( len(df6) > 0):
            st.subheader('Individuals with total project hours greater than 40 per week')
            st.warning('**Individuals found with total project hours greater than 40 per week', icon="⚠️")
            left_column, right_column = st.columns(2)
            with left_column:
                add_selectbox = st.selectbox('Select the project', psql.sqldf(""" SELECT DISTINCT td.Project FROM time_data td"""), key = 'select_option2')       
            st.table(df6[(df6['Project'] == add_selectbox)])
            st.markdown('---')
        else:
            st.write('No Records Found')

    if options == 'Hours Consumed from SOW':
        hours_consumed()
    elif options == 'Remaining Hours per Role':
        remaining_hours_per_role()
    elif options == 'Hours per An_Type per Day':
        hours_per_An_Type()
    elif options == 'Hours>8 for any Day':
        hours_greater_than_8_for_An_Type_for_any_day()
    elif options == 'Hours>40 per week':
        hours_greater_than_40_any_week()
    else:
        st.write("No Data")
else:
    st.info('Upload a file to proceed.', icon="ℹ️")


    



