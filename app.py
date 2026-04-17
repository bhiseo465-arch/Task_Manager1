import streamlit as st
import json
import os
from datetime import datetime, timedelta
import calendar
import requests
import pytz

# JSON Database file path
DB_FILE = "tasks.json"
TIMETABLE_FILE = "timetable.json"

# Weather API Configuration
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
IP_GEOLOCATION_API_URL = "https://ipapi.co/json/"
QUOTES_API_URL = "https://api.quotable.io/random"

def load_tasks():
    """Load tasks from JSON database"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_tasks():
    """Save tasks to JSON database"""
    with open(DB_FILE, 'w') as f:
        json.dump(st.session_state.tasks, f, indent=4, default=str)

def load_timetable():
    """Load timetable from JSON database"""
    if os.path.exists(TIMETABLE_FILE):
        try:
            with open(TIMETABLE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_timetable():
    """Save timetable to JSON database"""
    with open(TIMETABLE_FILE, 'w') as f:
        json.dump(st.session_state.timetable, f, indent=4, default=str)

def get_daily_quote():
    """Fetch daily inspirational quote from Quotable API"""
    try:
        response = requests.get(QUOTES_API_URL, timeout=5)
        data = response.json()
        return {
            "content": data.get("content", "Stay motivated!"),
            "author": data.get("author", "Unknown")
        }
    except:
        return {
            "content": "The only way to do great work is to love what you do.",
            "author": "Steve Jobs"
        }

def get_timezone_offset():
    """Get user's timezone offset"""
    try:
        response = requests.get(IP_GEOLOCATION_API_URL, timeout=5)
        data = response.json()
        return data.get("timezone", "UTC")
    except:
        return "UTC"

def get_city_coordinates(city_name):
    """Get latitude and longitude from city name"""
    try:
        params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        response = requests.get(GEOCODING_API_URL, params=params)
        data = response.json()
        if data.get("results"):
            result = data["results"][0]
            return result["latitude"], result["longitude"], result.get("name", city_name)
        return None
    except Exception as e:
        st.error(f"Error fetching city coordinates: {e}")
        return None

def get_user_location_from_ip():
    """Get user's location from IP address"""
    try:
        response = requests.get(IP_GEOLOCATION_API_URL, timeout=5)
        data = response.json()
        if data.get("city") and data.get("latitude") and data.get("longitude"):
            return {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "city": data["city"],
                "country": data.get("country_name", "")
            }
        return None
    except Exception as e:
        return None

def get_weather(latitude, longitude):
    """Fetch weather data from Open-Meteo API"""
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "timezone": "auto"
        }
        response = requests.get(WEATHER_API_URL, params=params)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching weather: {e}")
        return None

def get_weather_emoji(weather_code):
    """Convert WMO weather code to emoji"""
    code = int(weather_code)
    if code == 0 or code == 1:
        return "☀️"  # Clear
    elif code == 2 or code == 3:
        return "⛅"  # Partly cloudy
    elif code == 4:
        return "☁️"  # Overcast
    elif code in [45, 48]:
        return "🌫️"  # Foggy
    elif code in [51, 53, 55, 61, 63, 65]:
        return "🌧️"  # Rainy
    elif code in [71, 73, 75, 77, 80, 81, 82]:
        return "❄️"  # Snowy/Sleet
    elif code in [80, 81, 82]:
        return "⛈️"  # Thunderstorm
    else:
        return "🌤️"  # Default

def display_weather_widget():
    """Display weather widget in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌤️ Weather")
    
    # Initialize weather session state with IP-based location
    if 'weather_city' not in st.session_state:
        user_location = get_user_location_from_ip()
        if user_location:
            st.session_state.weather_city = user_location["city"]
            st.session_state.weather_lat = user_location["latitude"]
            st.session_state.weather_lon = user_location["longitude"]
        else:
            # Fallback to New York if IP detection fails
            st.session_state.weather_city = "New York"
            st.session_state.weather_lat = 40.7128
            st.session_state.weather_lon = -74.0060
    
    if 'weather_lat' not in st.session_state:
        st.session_state.weather_lat = 40.7128
    if 'weather_lon' not in st.session_state:
        st.session_state.weather_lon = -74.0060
    
    # City input
    city_input = st.sidebar.text_input(
        "Enter City",
        value=st.session_state.weather_city,
        placeholder="e.g., New York"
    )
    
    if st.sidebar.button("Update Weather"):
        coords = get_city_coordinates(city_input)
        if coords:
            st.session_state.weather_lat, st.session_state.weather_lon, city_name = coords
            st.session_state.weather_city = city_name
        else:
            st.sidebar.warning("City not found.")
    
    # Fetch and display weather
    weather_data = get_weather(st.session_state.weather_lat, st.session_state.weather_lon)
    
    if weather_data and "current" in weather_data:
        current = weather_data["current"]
        emoji = get_weather_emoji(current.get("weather_code", 0))
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        
        st.sidebar.markdown(f"""
        **{st.session_state.weather_city}**
        
        {emoji} **{temp}°F**
        
        💧 Humidity: {humidity}%
        💨 Wind: {wind} mph
        """)
    else:
        st.sidebar.info("Weather data unavailable")

def display_quote_widget():
    st.sidebar.markdown("---")
    st.sidebar.subheader("💭 Daily Quote")
    
    # Initialize quote session state
    if 'daily_quote' not in st.session_state:
        st.session_state.daily_quote = get_daily_quote()
        st.session_state.quote_date = datetime.now().date()
    
    # Refresh quote daily
    if datetime.now().date() != st.session_state.quote_date:
        st.session_state.daily_quote = get_daily_quote()
        st.session_state.quote_date = datetime.now().date()
    
    quote = st.session_state.daily_quote
    
    st.sidebar.markdown(f"""
    > *"{quote['content']}"*
    
    — **{quote['author']}**
    """)
    
    if st.sidebar.button("🔄 New Quote"):
        st.session_state.daily_quote = get_daily_quote()
        st.rerun()

def display_clock_widget():
    """Display live clock in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕐 Current Time")
    
    if 'user_timezone' not in st.session_state:
        st.session_state.user_timezone = get_timezone_offset()
    
    try:
        tz = pytz.timezone(st.session_state.user_timezone)
        current_time = datetime.now(tz).strftime("%H:%M:%S")
        current_date = datetime.now(tz).strftime("%A, %B %d, %Y")
        
        st.sidebar.markdown(f"""
        <div style='text-align: center; font-size: 24px; font-weight: bold;'>
        {current_time}
        </div>
        <div style='text-align: center; font-size: 12px;'>
        {current_date}
        </div>
        """, unsafe_allow_html=True)
    except:
        st.sidebar.write(f"⏰ {get_current_time()}")

# Initialize session state for tasks and timetable
if 'tasks' not in st.session_state:
    st.session_state.tasks = load_tasks()

if 'timetable' not in st.session_state:
    st.session_state.timetable = load_timetable()

st.title("📋 Task Manager")

# Display weather widget
display_weather_widget()

# Display quote widget
display_quote_widget()

# Display clock widget
display_clock_widget()

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Tasks", "Calendar View", "Timetable"])

if page == "Tasks":
    # Task input section
    col1, col2 = st.columns([2, 1])
    with col1:
        task = st.text_input("Enter Task")
    with col2:
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    
    due_date = st.date_input("Due Date (optional):")
    
    if st.button("Add Task"):
        if task:
            new_task = {
                "id": len(st.session_state.tasks) + 1,
                "task": task,
                "priority": priority,
                "due_date": str(due_date),
                "completed": False,
                "created_at": datetime.now().isoformat()
            }
            st.session_state.tasks.append(new_task)
            save_tasks()
            st.success(f"✅ Task '{task}' added with {priority} priority")
        else:
            st.error("❌ Please enter a task")
    
    st.divider()
    st.subheader("Your Tasks")
    
    if st.session_state.tasks:
        for i, t in enumerate(st.session_state.tasks):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                status = "✅" if t.get("completed") else "⭕"
                st.write(f"{status} {t['task']} | Priority: {t['priority']} | Due: {t.get('due_date', 'N/A')}")
            with col2:
                if st.button("Complete", key=f"complete_{i}"):
                    st.session_state.tasks[i]["completed"] = True
                    save_tasks()
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_{i}"):
                    st.session_state.tasks.pop(i)
                    save_tasks()
                    st.rerun()
    else:
        st.write("📭 No tasks yet...")

elif page == "Calendar View":
    st.subheader("📅 Calendar & Events")
    
    # Calendar selection
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.slider("Month", 1, 12, datetime.now().month)
    with col2:
        selected_year = st.slider("Year", 2024, 2027, datetime.now().year)
    
    # Display calendar
    cal = calendar.monthcalendar(selected_year, selected_month)
    month_name = calendar.month_name[selected_month]
    
    # Calendar header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"<h2 style='text-align: center;'>{month_name} {selected_year}</h2>", unsafe_allow_html=True)
    
    # Day of week headers
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    cols = st.columns(7)
    for i, day in enumerate(days):
        with cols[i]:
            st.markdown(f"<p style='text-align: center; font-weight: bold; color: #1f77b4;'>{day[:3]}</p>", unsafe_allow_html=True)
    
    # Calendar grid
    for week in cal:
        cols = st.columns(7)
        for day_idx, day in enumerate(week):
            with cols[day_idx]:
                if day == 0:
                    st.markdown("<div style='height: 120px; background-color: #f0f0f0; border: 1px solid #e0e0e0; border-radius: 5px;'></div>", unsafe_allow_html=True)
                else:
                    # Get tasks for this day
                    date_str = f"{selected_year:04d}-{selected_month:02d}-{day:02d}"
                    day_tasks = [t for t in st.session_state.tasks if t.get('due_date') == date_str]
                    
                    # Check if today
                    is_today = (day == datetime.now().day and 
                               selected_month == datetime.now().month and 
                               selected_year == datetime.now().year)
                    
                    # Color based on weekend or today
                    bg_color = "#fffacd" if is_today else ("#f5f5f5" if day_idx in [5, 6] else "white")
                    border_color = "#ff6b6b" if is_today else "#e0e0e0"
                    
                    # Calendar day box
                    task_html = f"<div style='height: 120px; background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 5px; padding: 8px; overflow-y: auto;'>"
                    task_html += f"<p style='margin: 0; font-weight: bold; color: #333;'>{day}</p>"
                    
                    # Add task indicators
                    for task in day_tasks[:2]:  # Show max 2 tasks
                        status = "✓" if task.get("completed") else "•"
                        color = "#999" if task.get("completed") else "#d32f2f"
                        priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(task.get("priority", "Low"), "🟢")
                        task_html += f"<p style='margin: 2px 0; font-size: 11px; color: {color}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{priority_emoji} {status}</p>"
                    
                    if len(day_tasks) > 2:
                        task_html += f"<p style='margin: 2px 0; font-size: 10px; color: #666;'>+{len(day_tasks)-2} more</p>"
                    
                    task_html += "</div>"
                    st.markdown(task_html, unsafe_allow_html=True)
                    
                    # Click to see details
                    if day_tasks:
                        with st.expander(f"View tasks for {month_name} {day}"):
                            for task in day_tasks:
                                status = "✅" if task.get("completed") else "⭕"
                                st.write(f"{status} **{task['task']}** ({task['priority']})")
    
    st.divider()
    
    # Show tasks by date
    st.subheader("📋 Tasks by Date")
    task_dates = {}
    for t in st.session_state.tasks:
        due_date = t.get('due_date', 'No date')
        if due_date not in task_dates:
            task_dates[due_date] = []
        task_dates[due_date].append(t)
    
    for date in sorted(task_dates.keys()):
        if date != 'No date':
            st.write(f"📌 **{date}**")
            for task in task_dates[date]:
                status = "✅" if task.get("completed") else "⭕"
                st.write(f"  {status} {task['task']} ({task['priority']})")
    
    if 'No date' in task_dates:
        st.write(f"📌 **No Date Assigned**")
        for task in task_dates['No date']:
            status = "✅" if task.get("completed") else "⭕"
            st.write(f"  {status} {task['task']} ({task['priority']})")

elif page == "Timetable":
    st.subheader("⏰ Daily Timetable")
    
    # Timetable date selection
    timetable_date = st.date_input("Select Date for Timetable", value=datetime.now().date(), key="timetable_date")
    date_key = str(timetable_date)
    
    # Initialize timetable for this date if not exists
    if date_key not in st.session_state.timetable:
        st.session_state.timetable[date_key] = {}
    
    # Create timetable layout
    st.markdown("### Create Your Hourly Schedule")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        hour = st.selectbox("Time (Hour)", range(24), format_func=lambda x: f"{x:02d}:00", key="hour_select")
    
    with col2:
        activity = st.text_input("Activity/Task", placeholder="e.g., Meeting, Lunch, Study", key="activity_input")
    
    with col3:
        if st.button("➕ Add to Timetable"):
            if activity:
                hour_key = f"{hour:02d}:00"
                st.session_state.timetable[date_key][hour_key] = activity
                save_timetable()
                st.success(f"✅ Added '{activity}' at {hour_key}")
                st.rerun()
            else:
                st.error("❌ Please enter an activity")
    
    st.divider()
    
    # Display timetable
    st.markdown("### 📅 Your Schedule")
    
    if st.session_state.timetable.get(date_key):
        # Create table data
        schedule_data = []
        for hour in range(24):
            hour_key = f"{hour:02d}:00"
            activity = st.session_state.timetable[date_key].get(hour_key, "—")
            schedule_data.append({
                "Time": hour_key,
                "Activity": activity,
                "Status": "Scheduled" if activity != "—" else "Free"
            })
        
        # Display as columns for better visualization
        col1, col2, col3 = st.columns(3)
        
        for idx, item in enumerate(schedule_data):
            if idx % 3 == 0:
                col = col1
            elif idx % 3 == 1:
                col = col2
            else:
                col = col3
            
            with col:
                if item["Activity"] != "—":
                    st.info(f"**{item['Time']}** - {item['Activity']}")
                    # Delete button
                    if st.button("❌ Remove", key=f"delete_schedule_{item['Time']}"):
                        del st.session_state.timetable[date_key][item['Time']]
                        save_timetable()
                        st.rerun()
                else:
                    st.write(f"**{item['Time']}** - *Free*")
        
        # Display as dataframe for better overview
        st.divider()
        st.markdown("### 📊 Schedule Overview")
        
        overview_data = []
        for hour in range(24):
            hour_key = f"{hour:02d}:00"
            activity = st.session_state.timetable[date_key].get(hour_key, "—")
            overview_data.append({"Time": hour_key, "Activity": activity})
        
        st.dataframe(overview_data, use_container_width=True, hide_index=True)
        
        # Clear schedule button
        if st.button("🗑️ Clear All Schedule for This Day"):
            st.session_state.timetable[date_key] = {}
            save_timetable()
            st.success("Schedule cleared!")
            st.rerun()
    
    else:
        st.write("📭 No activities scheduled for this day. Add one above!")
    
    # View statistics
    st.divider()
    st.markdown("### 📈 Schedule Statistics")
    
    all_dates = list(st.session_state.timetable.keys())
    if all_dates:
        total_activities = sum(len(activities) for activities in st.session_state.timetable.values())
        total_scheduled_hours = sum(len(st.session_state.timetable[d]) for d in all_dates)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scheduled Hours", total_scheduled_hours)
        with col2:
            st.metric("Total Activities", total_activities)
        with col3:
            st.metric("Dates with Schedule", len(all_dates))
    else:
        st.write("No timetables created yet!")