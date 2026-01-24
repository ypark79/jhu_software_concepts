Name: Youngmin Park (ypark79)

Modern Software Concepts in Python

Module Info: Module 1 Assignment: Personal Website 

Approach: 

Overview: I used PyCharm as any IDE and Python version 3.13.7 for this assignment. The initial website structure consisted of main.py, a templates folder that housed the html webpages, and a static folder that housed the biography photo. The main.py file imported the flask class and the templates, initiated the flask object (app), and contained all the routes to the html pages. Next step was to create a run.py file in order to  start the web application using the command $python run.py as per the assignment instructions. After the html webpages were completed as per the assignment instructions, a css file was created in the static folder and linked to all the webpages to add style edits. A single css file (main.css) was linked to all webpages. Lastly, a pages folder was created and a pages.py file was created within it to integrate a blueprint into the website infrastructure. The pages.py file houses the routes and templates for the webpage. Once the pages.py was created, the main.py and html pages were updated to properly link the blueprints to all the webpages. 

run.py – 
The function of run.py is to initiate the web application. Thus, the create_app function was imported from main.py and called in run.py to introduce an instance of Flask. Then the dunder main code was inserted to execute the web application when run.py is ran. 

main.py – 

The function of main.py is to instantiate the Flask class and generate a flask object (app). Additionally, main.py imports the blueprints from pages.py. The function of main.py is carried out by  a “create_app” function, which introduces the flask object and registers the blueprints contained in pages.py.

pages.py – 

Pages.py consolidates all the routes to all the pages within the webpage. It contains multiple functions which link the templates to all the webpages as well.  

html files – 

The web application contains three html files, one for each required webpage in accordance with the assignment instructions. The “head” section of each html page links to the main.css file, which integrates the style edits to each webpage. The first section of the “body” section is the navigation bar. This code includes both HTML and Jinja code – the HTML code creates the link to the different webpages and the Jinja code activates the css style attributes for when the user navigates to different webpages. In this case, this refers to the color of the navigation bar, and highlighting the webpage that the user is currently on. Lastly, the last section of the body is the titles, link to the biography photo, and the bio itself. The main.css linked in the “head” section of the html files controls the spacing rules of the website (bio text on left, bio photo on right, text and photo flush and centered, etc.). 

main.css – 

One css file was applied to all webpages; the majority of the style adjustments were designed while working on the home.html (About Me) page. ChatGPT was used to achieve specific style adjustments, which include adding color to the navigation bar, changing the color of each webpage link when the user hovers over it, and highlighting the tab with a different color when the user is on that webpage. The title fonts and sizes, spacing, as well as the positioning of the bio text and photo were achieved through css code retrieved from ChatGPT. 


Known Bugs: None

Citations: 

I referenced the code examples in the Module 1 Lecture slides to code run.py, main.py, and pages.py. This includes importing the Flask class, instantiating a Flask object, registering blueprints, and coding the routes to the html pages and webpages. I also referenced the code examples in the Module 1 Lecture slides when coding the navigation bar in the html files. For main.css file, I started with the code referenced in the Module 1 Lecture slides and then requested code in ChatGPT to achieve specific style adjustments that I desired. This included positioning the bio text and photo, making them flush, font style, coloring the navigation bar, and acquiring the Jinja code that activates highlights on the website links based on how the user navigates through my webpage. I also referenced ChatGPT to gain an conceptual understanding of how to code a link to my GitHub repo online.  Lastly, I referenced ChatGPT to acquire the code on how to insert comments in HTML and CSS files (<!-- --> and /*  */ respectively). 
