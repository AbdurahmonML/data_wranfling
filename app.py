from flask import Flask, render_template, jsonify, request
import sqlite3
import os
from prettytable import PrettyTable
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)
db_path = 'films.db'

# Initialize the SQLite database (without using SQLAlchemy)
import sqlite3

# Sample data to insert into the database
films_data = [
    ("The Shawshank Redemption", 1994, 28341469, "UK"),
    ("The Godfather", 1972, 250000000, "USA"),
    ("The Dark Knight", 2008, 1005973645, "USA"),
    ("Schindler's List", 1993, 322177000, "USA"),
    ("Pulp Fiction", 1994, 213928762, "USA"),
]

def init_db():
    def extract_alphabetic_substring(text):
        """
        Iterate over all characters in the string and stop when a non-alphabetical character is found.
        Return the substring from the start of the string up to that character.

        Args:
            text (str): The input string.

        Returns:
            str: The substring containing only alphabetical characters from the start.
        """
        if text[:13] == 'United States':
            return 'United States'
        if text[:14] == 'United Kingdom':
            return 'United Kingdom'
        for i, char in enumerate(text):
            if not char.isalpha() and char != ' ':  # Check if the character is non-alphabetical
                return text[:i]  # Return the substring up to the current index
        return text  # If all characters are alphabetical, return the entire string

    # Function to fetch HTML document
    def getHTMLdocument(url):
        response = requests.get(url)
        return response.content

    # Function to extract the country from the movie's Wikipedia page
    def get_country_from_movie_page(movie_url):
        movie_html = getHTMLdocument(movie_url)
        movie_soup = BeautifulSoup(movie_html, 'html.parser')
        
        # Find the infobox
        infobox = movie_soup.find('table', {'class': 'infobox'})
        
        # Find the row that contains the "Country" field
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                if header and 'Countries' in header.get_text():
                    # Extract the country from the next <td> tag
                    country_td = row.find('td')
                    if country_td:
                        country_text = country_td.get_text(strip=True)
                        return extract_alphabetic_substring(country_text)
                if header and 'Country' in header.get_text():
                    # Extract the country from the next <td> tag
                    country_td = row.find('td')
                    if country_td:
                        country_text = country_td.get_text(strip=True)
                        return extract_alphabetic_substring(country_text)
                        
        return "Country not found"


    def format_director_name(name):
        """Insert spaces between consecutive capital letters if needed."""
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', name)

    def get_director_from_movie_page(movie_url):
        movie_html = getHTMLdocument(movie_url)
        movie_soup = BeautifulSoup(movie_html, 'html.parser')
        
        # Find the infobox
        infobox = movie_soup.find('table', {'class': 'infobox'})
        
        # Find the row that contains the "Directed by" field
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                header = row.find('th')
                if header and 'Directed by' in header.get_text():
                    # Extract the director's name from the next <td> tag
                    director_td = row.find('td')
                    if director_td:
                        director_text = director_td.get_text(strip=True)
                        return format_director_name(director_text)  # Formats and returns the name
                        
        return "Director not found"

    # URL to scrape
    url_to_scrape = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"

    # Get the HTML document for the list of films
    html_document = getHTMLdocument(url_to_scrape)

    # Create BeautifulSoup object
    soup = BeautifulSoup(html_document, 'html.parser')

    # Find the table with class 'wikitable'
    table = soup.find('table', {'class': 'wikitable'})
    films_data = []
    # Loop through each row in the table (skipping the header row)
    for row in table.find_all('tr')[1:]:
        # Find the <th> element that contains the movie name
        movie_title = None
        revenue = None
        year = None
        country = "Unknown"
        directors = "Unknown"
        cnt = 0
        for i in row.find_all('td'):
            cnt += 1
            
            if cnt == 3:
                revenue = i.get_text(strip=True)
            
            if cnt == 4:
                year = i.get_text(strip=True)

        movie_name_tag = row.find('th')
        
        if movie_name_tag:
            movie_link = movie_name_tag.find('a')  # <a> inside <th>
            if movie_link:
                movie_title = movie_link.get_text(strip=True)  # Movie name
                movie_url = "https://en.wikipedia.org" + movie_link.get('href')  # Full URL
                
                # Get country for the movie
                country = get_country_from_movie_page(movie_url)
                directors = get_director_from_movie_page(movie_url)
                
        if movie_title and revenue and year:
            # Clean revenue to remove dollar signs and commas, then convert to int
            revenue = re.sub(r'[^\d]', '', revenue)
            revenue = int(revenue) if revenue else 0
            films_data.append((movie_title, directors, int(year), revenue, country))
        
        

    # Print the films_data before inserting into the database
    print("Films Data Before Insertion:")
    for film in films_data:
        print(film)

    # Check how many films we have before inserting them
    print(f"Films data length before inserting into DB: {len(films_data)}")

    # Connect to SQLite database (it will create the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop the table if it exists to clean up the database
    cursor.execute('DROP TABLE IF EXISTS films')

    # Create the table again with the correct schema (revenue as INTEGER)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            directors TEXT,
            year INTEGER,
            revenue INTEGER,  -- Revenue column as INTEGER
            country TEXT
        )
    ''')

    # Insert data from films_data list
    cursor.executemany('''
        INSERT INTO films (title, directors, year, revenue, country) 
        VALUES (?, ?, ?, ?, ?)
    ''', films_data)

    # Commit the changes
    conn.commit()

    # Display the contents of the database using PrettyTable
    cursor.execute('SELECT * FROM films')
    films = cursor.fetchall()
    
    print("Films in the Database:")
    table = PrettyTable(["ID", "Title", "Directors", "Year", "Revenue", "Country"])
    for film in films:
        table.add_row(film)
    print(table)

    # Check the number of films in the database after insertion
    cursor.execute('SELECT COUNT(*) FROM films')
    count = cursor.fetchone()[0]
    print(f"Films data length after inserting into DB: {count}")

    # Close the connection
    conn.close()

# Route to initialize the database
@app.route('/')
def home():
    init_db()
    return "Database initialized and ready!"

# Route to fetch films from the database and display them
@app.route('/films')
def films():
    # Fetch query parameters for filtering and sorting
    search_term = request.args.get('search', '').strip().lower()  # Filter by title
    sort_by = request.args.get('sort', 'year')  # Default sort by 'year'
    sort_order = request.args.get('order', 'asc')  # Default sort order is ascending

    # Create the SQL query with filtering and sorting
    query = 'SELECT * FROM films WHERE LOWER(title) LIKE ?'
    
    # Adding sorting logic
    if sort_order == 'asc':
        query += f' ORDER BY {sort_by} ASC'
    else:
        query += f' ORDER BY {sort_by} DESC'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute query with filtering
    cursor.execute(query, ('%' + search_term + '%',))
    films = cursor.fetchall()
    conn.close()

    return render_template('films.html', films=films, search_term=search_term, sort_by=sort_by, sort_order=sort_order)

# API route to fetch films as JSON (for dynamic JS rendering)
@app.route('/api/films')
def api_films():
    search_term = request.args.get('search', '').strip().lower()  # Trim and lowercase
    sort_by = request.args.get('sort', 'year')  # Default sort by 'year'
    sort_order = request.args.get('order', 'asc')  # Default sort order is ascending

    # Create the SQL query with filtering and sorting
    query = 'SELECT * FROM films WHERE LOWER(title) LIKE ?'
    
    # Adding sorting logic
    if sort_order == 'asc':
        query += f' ORDER BY {sort_by} ASC'
    else:
        query += f' ORDER BY {sort_by} DESC'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute query with filtering
    cursor.execute(query, ('%' + search_term + '%',))
    films = cursor.fetchall()
    conn.close()

    film_data = [
        {
            'title': film[1],
            'directors': film[2],
            'year' : film[3],
            'revenue': film[4],
            'country': film[5]
        }
        for film in films
    ]
    return jsonify(film_data)

if __name__ == '__main__':
    app.run(debug=True)
