from django.shortcuts import render,redirect
from django.core.files.storage import FileSystemStorage
import re
import pandas as pd
import os
from django.contrib import messages
from django.conf import settings

# patterns start:
pattern_id = r'[ID ]\w*:'
pattern1 = 'SQL Statement (Execute Time|Initial Fetch Time|Prepare Time) for SQL Cursor with ID \w*: \d*.\d* \w*'
pattern3 = r'ObjMgrLog	Error	\w*'
pattern4 = 'ID: Unknown\n'
pattern5 = r'ObjMgrSqlLog'
pattern7i = r'INSERT/UPDATE statement with ID:'
pattern8 = r'/app/siebel/'
pattern9 = r'ObjMgrSqlLog'
pattern10 = r'Bind variable \d: '
pattern11 = r':\d'
pattern12 = r'EventContext'
pattern13 = r'\n+'
# patterns end:

# global variable declarations start:
filename = ''
ifetch_id = ''
exe_id = ''
pre_id = ''
ifetch_time = ''
exe_time = ''
pre_time = ''
sql = ''
req = ''
splitstring = ''
idname = ''
valuename = ''
time_db = ''
eventcntxt = ''

all_time = []
Id = []

database_ifetch = pd.DataFrame()
database_exe_time = pd.DataFrame()
database_Prepare_Time= pd.DataFrame()

max_initial_fetch_time_gl = {}
max_execution_time_gl = {}
max_prepare_time_gl = {}

# global variable declarations end:

# Functions/Methods start:
def unique(l):
    unique_l = []
    for x in l:
        if x not in unique_l:
            unique_l.append(x)
    return unique_l

def choosetype(timetype):
    global splitstring, idname, valuename, time_db
    if timetype == "Initial Fetch Time":
        splitstring = 'Initial'
        idname = 'Cursor_Id_Ifetch'
        valuename = 'Initial_Fetch_Time'
        time_db = 'database_ifetch'
    elif timetype == "Execution Time":
        splitstring = 'Execute'
        idname = 'Cursor_Id_Exe'
        valuename = 'Execution_Time'
        time_db = 'database_exe_time'
    elif timetype == "Preparation Time":
        splitstring = 'Prepare'
        idname = 'Cursor_Id_Prep'
        valuename = 'Prepare_Time'
        time_db = 'database_Prepare_Time'
    else:
        print('timetype does not match')

def Cursor_time(Cursor_Id, timetype):
    row_number = []
    i = -1

    for l in time_db[idname]:
        i = i + 1
        if Cursor_Id in l:
            row_number.append(i)
    i = -1
    for time in time_db[valuename]:
        i = i + 1
        if i in row_number:
            print("Cursor Time: ", time)

def alltime():
    for match1 in re.finditer(pattern1, text):
        all_time1 = match1.group()
        all_time.append(all_time1)

def eventcontext():
    global text, pattern12, pattern13, sql
    sql = ''
    step = 0
    for match in re.finditer(pattern12,text):
        new_text = text[match.start():]
        for match2 in re.finditer(pattern13,new_text):
            new_text2 = new_text[:match2.end()]
            sql = sql + new_text2 + '\n'
            break

def fetchallid():
    global all_time

    for file in all_time:
        match = re.search(pattern_id, file)
        match2 = re.search('\w.*[^:]', match.group())
        Id.append(match2.group())
    all_Id = unique(Id)
    #print(len(all_Id))
    #print(all_Id)

def fetchtime(timetype):
    global all_time, splitstring

    fetchTime = []
    database_fetch_time = pd.DataFrame()
    fetch_time_id = []
    fetch_time = []
    choosetype(timetype)

    for time in all_time:
        if splitstring in time.split():
            fetchTime.append(time)

    for file in fetchTime:
        fetchTimeId1 = re.search('[ID ]\w*:', file)
        fetchTimeId = re.search('\w.*[^:]', fetchTimeId1.group())
        fetch_time_id.append(fetchTimeId.group())

        fetchTime = re.search(': \d*.\d*', file)
        fetchTime2 = re.search('(\d|\d\d).\d*', fetchTime.group())
        fetch_time.append(fetchTime2.group())

    database_fetch_time[idname] = fetch_time_id
    database_fetch_time[valuename] = fetch_time
    return database_fetch_time

def getmaxtime():
    global database_ifetch, database_exe_time, database_Prepare_Time, max_initial_fetch_time_gl, max_execution_time_gl, max_prepare_time_gl

    database_ifetch[['Initial_Fetch_Time']] = database_ifetch[['Initial_Fetch_Time']].apply(pd.to_numeric)
    database_exe_time[['Execution_Time']] = database_exe_time[['Execution_Time']].apply(pd.to_numeric)
    database_Prepare_Time[['Prepare_Time']] = database_Prepare_Time[['Prepare_Time']].apply(pd.to_numeric)

    max_initial_fetch_time_gl = database_ifetch.loc[database_ifetch['Initial_Fetch_Time'].idxmax()].to_dict()
    max_execution_time_gl = database_exe_time.loc[database_exe_time['Execution_Time'].idxmax()].to_dict()
    max_prepare_time_gl = database_Prepare_Time.loc[database_Prepare_Time['Prepare_Time'].idxmax()].to_dict()

    print("Maximum Initial fetch Time: ", max_initial_fetch_time_gl)
    print("Maximum Execution Time: ", max_execution_time_gl)
    print("Maximum Preparation Time: ", max_prepare_time_gl)


def fetch_query(text, req, qtype):
    global Cursor_Id, pattern4, pattern5, sql
    sql = ''
    Cursor_Id = str(req)
    if qtype == 'select':
        commonpattern6 = r'ID: ' + Cursor_Id + '\n'
        commonpattern7 = r'SELECT statement with ID: ' + Cursor_Id
    else:
        commonpattern6 = pattern4
        commonpattern7 = r'UPDATE statement with ID: Unknown'
    for match in re.finditer(commonpattern6, text):
        new_text = text[match.end() - (len(Cursor_Id) + 1):]
        for match2 in re.finditer(pattern5, new_text):
            query = new_text[:match2.start()]
            sql = sql + query
            break
    '''for match in re.finditer(commonpattern7, text):
        new_text1 = text[match.end():]
        for match2 in re.finditer(pattern8, new_text1):
            query_and_bind_variable = new_text1[:match2.start()]
            break

    for match in re.finditer(pattern5, query_and_bind_variable):
        query = query_and_bind_variable[:match.start()]
        bind_variable_text = query_and_bind_variable[match.end():]
        break

    bind_variable_list = []
    for lines in bind_variable_text.splitlines():
        for match in re.finditer(pattern10, lines):
            start = match.end()
            new_text = lines[start:]
            break

    i = 1
    line = []
    for lines in query.splitlines():
        if i != 1:
            line.append(re.sub(pattern11, 'Bind_Variable', lines.rstrip()))
        i = i + 1

    Updated_Query = "".join(line)
    print(Updated_Query)
    sql = Updated_Query'''
# Functions/Methods End:


def home(request):
    return render(request,'customupload.html')

def analyze(request):
    global filename
    global ifetch_id
    global exe_id
    global pre_id
    global ifetch_time
    global exe_time
    global pre_time
    global sql
    global req
    global splitstring
    global idname
    global valuename
    global time_db
    global all_time
    global Id
    global database_ifetch
    global database_exe_time
    global database_Prepare_Time
    global max_initial_fetch_time_gl
    global max_execution_time_gl
    global max_prepare_time_gl

    filename = ''
    ifetch_id = ''
    exe_id = ''
    pre_id = ''
    ifetch_time = ''
    exe_time = ''
    pre_time = ''
    sql = ''
    req = ''
    splitstring = ''
    idname = ''
    valuename = ''
    time_db = ''

    all_time = []
    Id = []

    database_ifetch = pd.DataFrame()
    database_exe_time = pd.DataFrame()
    database_Prepare_Time = pd.DataFrame()

    max_initial_fetch_time_gl = {}
    max_execution_time_gl = {}
    max_prepare_time_gl = {}

    if request.method == 'POST':
        print('Into Post Method')
        print(request.FILES)
        uploaded_file = request.FILES['myfile']
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
        print(uploaded_file.name)
        print(uploaded_file.size)
        print(settings.MEDIA_ROOT)

        filename = uploaded_file.name
        Analyzelog(filename,'maxtime')

        itimedict = max_initial_fetch_time_gl
        etimedict = max_execution_time_gl
        ptimedict = max_prepare_time_gl
        ifetch_id = itimedict['Cursor_Id_Ifetch']
        exe_id = etimedict['Cursor_Id_Exe']
        pre_id = ptimedict['Cursor_Id_Prep']

        ifetch_time = itimedict['Initial_Fetch_Time']
        exe_time = etimedict['Execution_Time']
        pre_time = ptimedict['Prepare_Time']

        return render(request,'result.html',
                      {'ifetch_id': ifetch_id, 'exe_id': exe_id,'pre_id': pre_id,
                       'ifetch_time': ifetch_time,'exe_time': exe_time,'pre_time': pre_time,
                       'sql': sql})


    return render(request,'customupload.html')

def fetchsql(request):
    print("Into Fetch Sql Block")
    CursorId = request.POST['CursorId']
    Analyzelog(filename,CursorId)
    return render(request, 'result.html',
                  {'ifetch_id': ifetch_id, 'exe_id': exe_id, 'pre_id': pre_id,
                   'ifetch_time': ifetch_time, 'exe_time': exe_time, 'pre_time': pre_time,
                   'sql': sql})

def evntcntxt(request):
    CursorId = 'eventcontext'
    Analyzelog(filename, CursorId)
    return render(request, 'result.html',
                  {'ifetch_id': ifetch_id, 'exe_id': exe_id, 'pre_id': pre_id,
                   'ifetch_time': ifetch_time, 'exe_time': exe_time, 'pre_time': pre_time,
                   'sql': sql})

def fetchinsertupdate(request):
    print("Into fetchinsertupdate Block")
    CursorId = 'Unknown'
    Analyzelog(filename,'Unknown')
    return render(request, 'result.html',
                  {'ifetch_id': ifetch_id, 'exe_id': exe_id, 'pre_id': pre_id,
                   'ifetch_time': ifetch_time, 'exe_time': exe_time, 'pre_time': pre_time,
                   'sql': sql})

def executiontime(request):
    clearhtml('exefile.html')
    createhtml(database_exe_time.to_html(),'exefile.html')
    return render(request,'exefile.html')

def initialfetchtime(request):
    clearhtml('initialfetchtime.html')
    createhtml(database_ifetch.to_html(),'initialfetchtime.html')
    return render(request,'initialfetchtime.html')

def preparetime(request):
    clearhtml('preparetime.html')
    createhtml(database_Prepare_Time.to_html(),'preparetime.html')
    return render(request,'preparetime.html')

def createhtml(timedf,filename):
    template_path = settings.TEMPLATE_DIRECTORY
    filepath = template_path + filename
    timefile = open(filepath,"w")
    timefile.write(timedf)
    timefile.close()

def clearhtml(filename):
    template_path = settings.TEMPLATE_DIRECTORY
    filepath = template_path + filename
    timefile = open(filepath,"w")
    timefile.truncate(0)

def Analyzelog(filename,req):
    global text, database_ifetch, database_exe_time, database_Prepare_Time

    currentpath = os.getcwd()
    filepath = settings.MEDIA_ROOT_PATH + filename
    logFile = open(filepath)
    text = logFile.read()

    alltime()
    database_ifetch = fetchtime('Initial Fetch Time')
    database_exe_time = fetchtime('Execution Time')
    database_Prepare_Time = fetchtime('Preparation Time')
    fetchallid()
    if req == 'maxtime':
        getmaxtime()
    elif req == 'Unknown':
        fetch_query(text, req, 'Unknown')
    elif req == 'eventcontext':
        eventcontext()
    else:
        fetch_query(text, req, 'select')
