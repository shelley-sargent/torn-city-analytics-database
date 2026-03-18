# Torn API Automation

This project is designed to regularly pull and store data from Torn City's REST API. The goal is to track individual and faction progress over time, and to create a usable resource for faction administrators to access performance information for both publication and analysis.

Torn City is a social browser-based MMO that requires coordinated gameplay within different groups known as "factions". To be successful, faction leadership needs to be able to see overall progress and participation as well as individual strengths and weaknesses to identify issues and help players maximize their performance.

## Current Implementation

Currently, the pipeline pulls two different datasets and runs them via cron at different intervals:
- **Member statistics** (hourly) - tracks individual faction member progression
- **Attack logs** (every 6 hours) - analyzes incoming and outgoing attacks across the faction

The data is stored via PostgreSQL on a local Linux server.

## Project Goals

### Short-term
Create a Fast API app that allows other leaders to easily access the information either via API or through CSVs. This app needs to cater to varying degrees of technical ability and a wide variety of data queries.

### Long-term
Use unsupervised machine learning to analyze both attack outcomes and player statistics to predict the outcome of a fight between two individuals.

## Using the Script

### Prerequisites
- Access to a PostgreSQL database (local server or cloud platform like Supabase)
- Torn City API key(s)
- Python 3.x installed
- Linux/Unix system with cron (e.g., Raspberry Pi)

### Setup

1. **Clone the repository**
```bash
   git clone https://github.com/your-username/torn-api-automation.git
   cd torn-api-automation
```

2. **Install dependencies**
```bash
   pip install -r requirements.txt
```

3. **Configure environment variables**
   
   Edit `.env.example` and save it as `.env`:
```bash
   # API Configuration
   API_KEYS={"username": "your_api_key", "username2": "your_api_key2"}  # Supports multiple keys; script selects randomly
   FACTION=12345  # Your faction ID
   
   # Database Configuration
   DB_HOST=your-database-host
   DB_NAME=your-database-name
   DB_USER=your-username
   DB_PASSWORD=your-password
   DB_PORT=5432
```

4. **Set up database schema**

Create the database and user in PostgreSQL, then run the schema file:
```bash
   sudo -u postgres psql
```
```sql
   CREATE DATABASE tornbot;
   CREATE USER tornbot_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE tornbot TO tornbot_user;
   \q
```
   Then apply the schema:
```bash
   sudo -u postgres psql -d tornbot -f schema.sql
```
   


5. **Configure cron jobs**
```bash
   crontab -e
```
   
   Add the following lines:
```bash
   0 */6 * * * /usr/bin/python3 /path/to/file/attacks.py >> /path/to/file/cron.log 2>&1
   0 * * * * /usr/bin/python3 /path/to/file/players.py >> /path/to/file/cron.log 2>&1
   */5 * * * * /usr/bin/python3 /path/to/file/ranked_war.py >> /path/to/file/cron.log 2>&1
```

## Skills Demonstrated

- **Python** - Core scripting language
- **Pandas** - Data manipulation and transformation
- **Data Cleaning** - Handling missing values, type conversions, normalization
- **REST API** - Integration with Torn City API
- **Cron** - Automated task scheduling
- **PostgreSQL** - Relational database management
- **psycopg2** - Database connectivity

## License

Copyright (c) 2026 Shelley Sargent

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contact

[GitHub](https://www.github.com/shelley-sargent) | [Email](shelleysargent0@gmail.com)
