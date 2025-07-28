# **FastAPI Chat Application – Backend Documentation Group A and B**

## **Project Overview**

This is the backend for a **real-time chat application** built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **WebSockets**, featuring:

- **JWT authentication** for secure user login
- **Role-based access control (RBAC)** with **admin** and **user** roles
- **Persistent messaging** stored in PostgreSQL
- **Real-time communication** with WebSocket rooms
- **Analytics endpoints** for monitoring chat activity
- **Admin dashboard** powered by **SQLAdmin** for managing users, rooms, and messages

---

## **System Architecture**

**Flow**:

1. **Client** (browser or Postman) → **FastAPI server** (REST & WebSockets)
2. **Authentication** handled with JWT tokens.
3. **Data persistence** with PostgreSQL using SQLAlchemy ORM.
4. **Admin Panel** provides a secure UI for viewing and managing all data.

---

## **Key Features**

### **1. User Management**

- **Signup** (`POST /signup`): First registered user becomes **admin**, others are **users**.
- **Login** (`POST /login`): Returns a **JWT token**.
- **Protected route** (`GET /protected`): Verifies any authenticated user.
- **Admin-only route** (`GET /admin-only`): Accessible only by admins.

### **2. Room Management**

- **Create room** (`POST /rooms`): Admin-only.
- **List rooms** (`GET /rooms`): Available to all users.

### **3. Real-Time Chat**

- Connect via WebSocket:
    
    ```
    
    ws://localhost:8000/ws/{room_id}?token=<JWT_TOKEN>
    
    ```
    
- **Authentication**: JWT passed in the query string.
- **Recent history**: Last 20 messages loaded on connection.
- **Broadcast**: Messages are delivered to all connected clients.

### **4. Analytics Endpoints**

- **Messages per room**: `GET /analytics/messages-per-room`
- **User activity**: `GET /analytics/user-activity`
- **CSV export**: `GET /analytics/messages-per-room/csv`
- All analytics endpoints require **admin role**.

### **5. Admin Dashboard**

- Available at `http://localhost:8000/admin`.
- Features:
    - Manage **Users, Rooms, and Messages**.
    - Displays related data (e.g., message sender username, room name).
- **Authentication**: Uses JWT to ensure only admins access the panel.

---

## **Tech Stack**

- **Backend Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (HS256) using `python-jose`
- **Password Hashing**: `passlib[bcrypt]`
- **Admin Interface**: SQLAdmin
- **Environment Variables**: `python-dotenv`

---

## **Setup Instructions**

### **1. Clone Repository**

```bash

git clone <your_repo_url>
cd chat-app

```

### **2. Create Virtual Environment**

```bash

python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

```

### **3. Install Dependencies**

```bash

pip install -r requirements.txt

```

### **4. Configure Environment Variables**

Create `.env` in the root folder:

```

SECRET_KEY=your_secret_key
ALGORITHM=HS256
DATABASE_URL=postgresql://user:password@localhost:5432/chatdb

```

### **5. Initialize Database**

```bash

>>> from database import Base, engine
>>> Base.metadata.create_all(bind=engine)
>>> exit()

```

### **6. Start Server**

```bash

uvicorn main:app --reload

```

Visit: [http://127.0.0.1:8000](http://127.0.0.1:8000/)

---

## **Testing the Application**

### **1. Sign up a user**

```

POST /signup
{
  "username": "admin",
  "password": "password123"
}

```

**First user automatically becomes admin.**

### **2. Login**

```

POST /login
{
  "username": "admin",
  "password": "password123"
}

```

Response:

```json

{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}

```

### **3. Access Admin Panel**

- Navigate to: `http://localhost:8000/admin`
- Use your JWT token; only admins are authorized.

### **4. Create Rooms and Chat**

- **Create room**: `POST /rooms` (admin only).
- **Connect to WebSocket**:
    
    `ws://localhost:8000/ws/{room_id}?token=<JWT_TOKEN>`
    

---

## **Validation & Testing Results**

- ✅ **RBAC** verified (admin vs user access).
- ✅ **JWT authentication** confirmed.
- ✅ **WebSocket messaging** works with persistence.
- ✅ **Admin dashboard** displays users, rooms, and messages.
- ✅ **Analytics endpoints** return correct data and CSV exports.

## Group C

# **Sentiment Analysis on IMDb & Twitter Reviews**

## **Project Overview**

This project builds a **sentiment analysis model** to classify movie and Twitter reviews as **positive** or **negative**.

We use two datasets:

- [IMDb Movie Reviews Dataset (50k reviews)](https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews)
- [Twitter Sentiment140 Dataset (1.6M tweets)](https://www.kaggle.com/datasets/kazanova/sentiment140)

The pipeline includes **data cleaning, text preprocessing, TF-IDF vectorization, model training, evaluation, and model export**.

---

## **Tech Stack**

- **Language:** Python
- **Environment:** Jupyter Notebook
- **Libraries:**
    - `pandas`, `numpy` – data processing
    - `matplotlib`, `seaborn` – visualization
    - `scikit-learn` – ML model & TF-IDF
    - `nltk` – text preprocessing
    - `joblib` – model saving

---

## **Steps Implemented**

### 1. **Data Collection**

- Loaded IMDb and Twitter datasets into pandas DataFrames.
- Combined datasets for a balanced set of **positive** and **negative** examples.

### 2. **Data Cleaning & Preprocessing**

- Removed duplicates and null values.
- Lowercased text.
- Removed punctuation, stopwords, and special characters.
- Tokenized and lemmatized reviews for better feature representation.

### 3. **Feature Extraction**

- Used **TF-IDF Vectorizer** from `scikit-learn` to convert cleaned text into numerical feature vectors.
- Limited vocabulary size and removed extremely rare/overly common terms.

### 4. **Model Training**

- Used **Logistic Regression** for binary sentiment classification.
- Split data into **training** (80%) and **testing** (20%) sets.

### 5. **Model Evaluation**

- Evaluated using **accuracy**, **precision**, **recall**, and **F1-score**.
- Visualized **confusion matrix** and **class distribution**.

### 6. **Model Saving**

- Saved the trained model as `sentiment_model.pkl`.
- Saved the TF-IDF vectorizer as `tfidf_vectorizer.pkl`.
