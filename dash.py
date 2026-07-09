import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split as tts
from sklearn.preprocessing import LabelEncoder as lb
from sklearn.ensemble import RandomForestRegressor as rfr
from sklearn.metrics import r2_score,mean_absolute_error,mean_squared_error


st.set_page_config(page_title="Business Analysis Dashboard")

conn=sqlite3.connect("Data.db")
cursor=conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,password TEXT)
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,dataset_name TEXT,algorithm TEXT,prediction REAL,date TEXT)
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,prediction REAL)
""")
conn.commit()

if "login" not in st.session_state:
    st.session_state.login=False

if "user" not in st.session_state:
    st.session_state.user=""

if "dataset" not in st.session_state:
    st.session_state.dataset=None

if "model" not in st.session_state:
    st.session_state.model=None

if "accuracy" not in st.session_state:
    st.session_state.accuracy=None

if "label_encoders" not in st.session_state:
    st.session_state.label_encoders={}


menu=st.sidebar.selectbox(
    "Dashboard",
    [
        "Home",
        "Register",
        "Login",
        "Dataset Upload",
        "Data Preprocessing",
        "Data Filtering",
        "Model Training",
        "Sales Prediction",
        "Dashboard",
        "Visualizations",
        "Prediction History",
        "Profile",
        "Logout"
    ]
)

if menu=="Home":
    st.title("Wellcome on Bussiness Analysis Board")
    st.write("This application allow user to :")
    st.write("Register & Login")
    st.write("Uploade There Dataset")
    st.write("cleaning of dataset")
    st.write("training of ml model")
    st.write("Predict Sales")
    st.write("View Business Dashboard")
    st.write("Generate Chart ")
    st.write("Save Prediction History")
    st.write("Manage Profile")

    st.info("Use Sidebar selectbox to navigate through the application.")

if menu=="Register":
    st.title("Registration Page")

    username=st.text_input("Enter username")
    password=st.text_input("Enter new password",type='password')

    if st.button("Register"):

        if username=="" or password=="":
            st.error("Please fill all the field")
        else:
            cursor.execute("SELECT * FROM user WHERE username=?",(username,))
            user=cursor.fetchone()
            if user:
                st.warning("Username Allready Exists.")
            else:
                cursor.execute("INSERT INTO user(username,password) VALUES(?,?)",(username,password))
                conn.commit()
                st.success("Registration Successfull.")
    
if menu=="Login":
    st.title("Login Page")

    username=st.text_input("Enter Username")
    password=st.text_input("Enter Password",type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM user WHERE username=? and password=?",(username,password))
        user=cursor.fetchone()

        if user:
            st.session_state.login=True
            st.session_state.user=username

            st.success("Login Successfull.")
            
        else:
            st.error("Invalid username or password")

if menu=="Dataset Upload":
    if not st.session_state.login:
        st.warning("Login FIrst")
    else:
        st.title("Uploaded Dataset")
        option=st.radio("Choose Dataset",["Sample Dataset","Upload CSV","Upload Excel"])

        if option=="Sample Dataset":
            sample={
                "Product":["Laptop","Mobile","Mouse","Table","Printer"],
                "Category":["Electronics","Electronics","Accessories","Office","Accessories"],
                "Region":["South","North","West","East","South"],
                "Price":[56000,25000,1500,5000,10000],
                "Qty":[5,10,15,20,11],
                "Sales":[280000,250000,22500,100000,110000],
                "Profit":[12000,4000,300,2500,3000]
            }
            df=pd.DataFrame(sample)
            st.session_state.dataset=df
            st.dataframe(df)
            st.success("Sample Dataset Loaded")
        elif option=="Upload CSV":
            file=st.file_uploader("Upload csv",type=['csv'])

            if file is not None:
                uploaded_df=pd.read_csv(file)
                st.success("Csv Uploaded Successfully.")
                st.dataframe(uploaded_df)
                st.session_state.dataset=uploaded_df
        elif option=="Upload Excel":
            file=st.file_uploader("Upload Excel file",type=['xlsx'])
            if file is not None:
                uploaded_df=pd.read_excel(file)
                st.success("Excel File Uploaded.")
                st.dataframe(uploaded_df)
                uploaded_df=st.session_state.dataset

if menu=="Data Preprocessing":
    if not st.session_state.login:
        st.warning("Please Login First")
        st.stop()
    st.title("Data Preprocessing (Cleaning)")
    if st.session_state.dataset is None:
        st.warning("Please Uploade Dataset.")
    else:
        df=st.session_state.dataset.copy()

        st.subheader("Dataset Preview")
        st.dataframe(df)

        st.write("Number of Rows ",df.shape[0])
        st.write("Number of Columns ",df.shape[1])

        st.subheader("Missing Values")
        st.write(df.isnull().sum())

        if st.button("Remove Missing Values"):
            df=df.dropna()
            st.session_state.dataset=df
            st.success("Missing Values Removed")
            st.dataframe(df)
        if st.button("Remove Duplicated Rows"):
            df=df.drop_duplicates()
            st.session_state.datset=df
            st.success("Duplicate Rows Removed")
            st.dataframe(df)
        st.subheader("Summary Statistics")
        st.dataframe(df.describe())

        target=st.selectbox("Select Target Column",df.columns)

        feature=st.multiselect("Select Feature Columns",df.columns)

        st.session_state.target=target
        st.session_state.feature=feature

if menu=="Data Filtering":
    if not st.session_state.login:
        st.warning("Please Login First")
        st.stop()
    st.title("Data Filtering")
    if st.session_state.dataset is None:
        st.warning("Please Uploade Dataset.")
        st.stop()
    df=st.session_state.dataset
    column=st.selectbox("Select Column ",df.columns)
    value=st.multiselect("Select Value",df[column].unique(),default=df[column].unique())
    filtered_data=df[df[column].isin(value)]
    st.dataframe(filtered_data)
    st.session_state.dataset=df

    csv=filtered_data.to_csv(index=False)

    st.download_button(
        label="Downlode Filtered Dataset",
        data=csv,
        file_name="filtered.csv",
        mime="text/csv"
    )

if menu=="Model Training":
    if not st.session_state.login:
        st.warning("Please Login First.")
        st.stop()
    
    st.title("Machine Learning Model Training")

    if st.session_state.dataset is None:
        st.warning("Please Uploade Dataset.")
    df=st.session_state.dataset.copy()

    if "feature" not in st.session_state or "target" not in st.session_state:
        st.warning("Please complate data preprocessing first")
        st.stop()

    feature=st.session_state.feature
    target=st.session_state.target


    x=df[feature].copy()
    y=df[target]

    label_encoder={}

    for column in x.select_dtypes(include="object").columns:
        encoder=lb()
        x[column] = encoder.fit_transform(x[column])
        label_encoder=encoder
        st.session_state.label_encoders=label_encoder
    x_train,x_test,y_train,y_test=tts(x,y,test_size=0.2,random_state=42)

    if st.button("Train Model"):
        model=rfr(n_estimators=100,random_state=42)
        model.fit(x_train,y_train)

        prediction=model.predict(x_test)

        accuracy=r2_score(y_test,prediction)
        mae=mean_absolute_error(y_test,prediction)
        mse=mean_squared_error(y_test,prediction)

        st.session_state.model=model
        st.session_state.accuracy=accuracy

        st.write("Model Preformance")

        st.write("R2 Score :",accuracy)
        st.write("MAE is  :",mae)
        st.write("MSE id  :",mse)
        st.write("Prediction is :",prediction)


if menu=="Sales Prediction":
    if not st.session_state.login:
        st.warning("Login First.")
        st.stop()
    st.title("Sales Prediction")
    if st.session_state.model is None:
        st.warning("Please complate model prediction process.")
        st.stop()
    df=st.session_state.dataset
    feature=st.session_state.feature
    model=st.session_state.model

    input_data=[]
    for col in feature:
        if df[col].dtype=="object":
            value=st.selectbox(col,df[col].unique())
            encoder=st.session_state.label_encoders[col]
            value=encoder.transform([value])[0]
        else:
            value=st.number_input(col,value=float(df[col].mean()))
        input_data.append(value)
    if st.button("Predict Sales"):
        prediction=model.predict([input_data])[0]
        st.success(f"Predicted Sales = {round(prediction,2)}")

        cursor.execute("INSERT INTO prediction(username,prediction) VALUES (?,?)",(st.session_state.user,float(prediction)))
        conn.commit()            
if menu=="Dashboard":
    if not st.session_state.login:
        st.warning("Login First.")
        st.stop()
    st.title("Business Analysis")
    if st.session_state.model is None:
        st.warning("Please complate model prediction process.")
        st.stop()
    df=st.session_state.dataset
    st.subheader("User Profile")
    st.write("User is ",st.session_state.user)

    numeric_columns=df.select_dtypes(include="number").columns
    if len(numeric_columns) >0:
        selected=st.selectbox("Select Numeric Column",numeric_columns)
        c1,c2=st.columns(2)

        with c1:
            st.metric("Total",df[selected].sum())
            st.metric("Average",df[selected].mean())
        with c2:
            st.metric("Minimum",df[selected].min())
            st.metric("Maximum",df[selected].max())
    st.subheader("Dataset Preview")
    st.dataframe(df)

if menu=="Visualizations":
    if not st.session_state.login:
        st.warning("Login First.")
        st.stop()
    st.title("Business Analysis")
    if st.session_state.model is None:
        st.warning("Please complate model prediction process.")
        st.stop()
    df=st.session_state.dataset

    chart=st.selectbox("Select Chart Type",["Bar Chart","Line","Histogram","Pie"])
    numeric_columns=df.select_dtypes(include="number").columns.tolist()
    all_columns=df.columns.tolist()

    if chart=="Bar Chart":
        x= st.selectbox("x-axis",all_columns)
        y=st.selectbox("y-axis",numeric_columns)

        fig,ax=plt.subplots()
        ax.bar(df[x],df[y])

        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title("Bar Chart")
        st.pyplot(fig)
    elif chart=="Line":
        x= st.selectbox("x-axis",all_columns)
        y=st.selectbox("y-axis",numeric_columns)

        fig,ax=plt.subplots()
        ax.plot(df[x],df[y])

        ax.set_title("Line Chart")
        st.pyplot(fig)
    elif chart=="Histogram":
        column=st.selectbox("Numeric Column",numeric_columns)
        fig,ax=plt.subplots()

        ax.hist(df[column],bins=10)
        ax.set_title("Histogram")
        st.pyplot(fig)
    elif chart=="Pie":
        column=st.selectbox("Categort Columns",all_columns)
        value=df[column].value_counts()
        fig,ax=plt.subplots()

        ax.pie(value,labels=value.index,autopct="%1.1f%%")
        ax.set_title("Pie Chart")
        st.pyplot(fig)
    

            
if menu=="Prediction History":
    if not st.session_state.login:
        st.warning("Please Login First.")
        st.stop()
    st.title("Prediction History")
    cursor.execute("SELECT * FROM prediction WHERE username=?",(st.session_state.user,))
    history=cursor.fetchall()

    if len(history)==0:
        st.info("No Prediction History Found")
    else:
        history_df=pd.DataFrame(history,columns=["id","username","prediction"])
        st.dataframe(history_df)
if menu=="Profile":
    if not st.session_state.login:
        st.warning("Please Login First.")
    st.title("User Profile")
    st.subheader("Account Information")
    st.write("Username :",st.session_state.user)

    if  st.session_state.dataset is not None:
        st.write("Dataset Uploded : Yes")
    else:
        st.write("Dataset Uploded : No")
    
    if st.session_state.model is not None:
        st.write("Machine Learning Model : Trained")
    else:
        st.write("Machine Learning Model : Not Trained")
    
    if st.session_state.accuracy is not None:
        st.write("Model Accuracy :",st.session_state.accuracy)
    else:
        st.write("Model Accuracy : Not Availabel")

if menu=="Logout":
    if not st.session_state.login:
        st.warning("Please Login First.")
    else:
        st.session_state.login=False
        st.session_state.user=""
        st.session_state.datset=None
        st.session_state.model=None
        st.session_state.accuracy=None
        st.session_state.label_encoders=None

        st.success("Logout Successfully.")
    