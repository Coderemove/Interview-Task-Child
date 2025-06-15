import datetime
import subprocess
import sys
import webbrowser
import os
from bs4 import BeautifulSoup
from path_utils import get_output_path, DIRECTORY_KEYS

def create_report_qmd():
    # Collect required system and project information
    report_title = "Instagram Data Analysis Report"
    author = "Szymon Fedyk"
    # Use ISO format YYYY-MM-DD so Quarto will display the correct date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
   
    # Check if graphs directory exists using path_utils
    try:
        # This will create the graphs directory if it doesn't exist and validate the path
        graphs_dir = get_output_path(DIRECTORY_KEYS['GRAPHS'], '')
        graphs_dir = os.path.dirname(graphs_dir)  # Remove empty filename part
        
        # Check if any graph files exist
        graph_files = ['graph1.png', 'graph2_monthly.png', 'graph3.png', 'graph4_female.png', 'graph4_male.png', 'graph4_undefined.png']
        missing_graphs = []
        for graph_file in graph_files:
            graph_path = os.path.join(graphs_dir, graph_file)
            if not os.path.exists(graph_path):
                missing_graphs.append(graph_file)
        
        if missing_graphs:
            print(f"WARNING: Missing graph files: {missing_graphs}")
            print("Some graphs may not display in the report. Please run the analysis scripts first.")
        
    except Exception as e:
        print(f"ERROR: Cannot access graphs directory: {e}")
        print("Please run master.py first to set up the project structure!")
        sys.exit(1)

    # Define the QMD content with placeholders using relative paths from project root
    report_content = f"""---
title: "{report_title}"
author: "{author}"
date: "{date_str}"
format: html
theme: lumen
---

# Overview

This report was generated using code in the repository <https://github.com/Coderemove/Interview-Task-Child>.

# Project Information

This project was made by Szymon Fedyk as part of an interview task for My Thriving Child. The goal was to analyze Instagram data and generate insights as per the instructions provided.
   
# Instagram Data Analysis

## Cleaning
The first process of analysis was cleaning the dataset. I used python to check for duplication (by using row hashes and other tests), and removed any duplication found. 
I also split the xlsv file into csv files for easier manipulation in pandas.
I also dropped any columns that were unneeded, and removed the queries sheet from the project as it seemed to be some form of query log from whatever service was used to collect and query this data.

## Engagement on Instagram
I used the Instagram Post Engagement dataset to calculate the average engagement on the post, and then grouped them into weeks and months to analyze the changes in engagement over time. 
I used a t-test to determine if there was a significant change in engagement between the weeks, and that allowed me to identify any significant month.
I found that the only month that had significance was 2024-11, and so I decided to focus on that month for more in-depth analysis.

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph1.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Graph 1 not found. Please run the average engagement analysis script.")
```

## Media Reach impact on Engagement 
As I had found out that the engagement on Instagram had a significant drop in November 2024, I decided to analyze the media reach of the posts for the whole dataset.
Interestingly, I did not find any significant difference in the media reach of the posts between the months.

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph2_monthly.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Graph 2 (monthly) not found. Please run the media reach analysis script.")
```

To allow a fair comparison between the media reach and engagement, I also tested for significance between the weekly and monthly media reach, and found that there was no significant difference between the two.
Therefore, it's fair to say that media reach doesn't have a clear impact on engagement.
If you are interested in the exact statistical values, they are available in the logs.

## Reels vs Feed Posts
I found a potential lead on why the engagement dropped on 2024-11. There was a significant increase in posts.

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph3.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Graph 3 not found. Please run the feed vs reel analysis script.")
```

Now, the data sample is a bit too small for it to be statistically significant, therefore it could be an unrelated, but a massive increase of posts does correlate with a decrease of engagement. 
However, the overall media reach of posts for the month did not change. It is possible that the decrease in engagement, and the same levels of media reach, could have resulted in a drop of visibility of the account.
Some websites do suggest that Instagram will reduce the visibility of accounts that post too much, and so it is possible that this is the case here.
Furthermore, the decrease in engagement could have swayed the algorithm to show less of the posts.

## Possible Solutions

**Diversify the social media websites used to promote the content.**
One of the possible solutions I thought of, upon checking the age demographics, was to look into why that demographic might not be as engaged with Instagram.

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph4_female.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Female age demographics graph not found. Please run the age analysis script.")
```

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph4_male.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Male age demographics graph not found. Please run the age analysis script.")
```

```{{python}}
import os
from IPython.display import Image, display
img_path = os.path.join("graphs", "graph4_undefined.png")
if os.path.exists(img_path):
    display(Image(filename=img_path))
else:
    print("Undefined gender demographics graph not found. Please run the age analysis script.")
```

This paper <https://onlinelibrary.wiley.com/doi/abs/10.1002/mar.21499> suggests that one of the factors in why the users might not engage with content is lack of privacy and trust in the platform and the advertiser.
Furthermore, <https://www.statista.com/statistics/1440802/privacy-actions-taken-internet-users-global-by-age/#:~:text=As%20of%20June%202023%2C%20roughly%2038%20percent,steps%20regarding%20their%20privacy%20on%20the%20internet.> shows that 45% of the largest user age group cares about privacy on the internet.
Since last year, Instagram has been under fire for its privacy policies, and so it is possible that the users are not engaging with the content due to that.
   
I have not looked into the linked facebook dataset, due to the limitations of the timeframe, but one of the possible solutions would be to post the media content onto Tiktok.
It's not to say that Tiktok is a perfect, or even better platform when it comes to privacy, but it is still a platform with a very large user base.
   
"""
    
    # Save the report file to project root using safe path management
    try:
        report_path = get_output_path('..', "report.qmd")  # Save to project root
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✓ Created report.qmd at: {report_path}")
        return report_path
    except Exception as e:
        print(f"Error creating report.qmd: {e}")
        sys.exit(1)

def render_report():
    try:
        # Change to project root directory for rendering
        original_dir = os.getcwd()
        project_root = os.path.dirname(original_dir)
        
        try:
            os.chdir(project_root)
            
            # Validate command
            allowed_commands = ["quarto"]
            if "quarto" not in allowed_commands:
                raise ValueError("Command not allowed")
            
            # Render the Quarto report
            subprocess.run(["quarto", "render", "report.qmd"], check=True, shell=False)
            print("✓ Report generated successfully.")
            
            # Return path to the generated HTML file
            return os.path.join(project_root, "report.html")
            
        finally:
            # Always return to original directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        print(f"Error generating report: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during report rendering: {e}")
        sys.exit(1)

def inject_mode_buttons(report_html_path):
    try:
        # Validate that the HTML file exists
        if not os.path.exists(report_html_path):
            raise FileNotFoundError(f"Report HTML file not found: {report_html_path}")
        
        # Open the existing report.html file
        with open(report_html_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")

        # Define the snippet to inject
        mode_buttons_html = """
<style>
  /* Dark mode styling */
  .dark-mode {
    background-color: #121212;
    color: #ffffff;
  }
  /* Invert colours of images (graphs) in dark mode */
  .dark-mode img {
    filter: invert(1) hue-rotate(180deg);
  }
  /* Style for the toggle buttons */
  .mode-toggle {
    margin: 0.5rem;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }
</style>

<div id="mode-buttons">
  <button id="btn-light" class="mode-toggle btn btn-light">Light Mode</button>
  <button id="btn-dark" class="mode-toggle btn btn-dark">Dark Mode</button>
</div>

<script>
  // Toggle dark mode on button clicks
  document.getElementById("btn-light").addEventListener("click", function() {
    document.body.classList.remove("dark-mode");
  });
  document.getElementById("btn-dark").addEventListener("click", function() {
    document.body.classList.add("dark-mode");
  });
</script>
"""
        # Insert the snippet at the top of the body tag
        if soup.body:
            soup.body.insert(0, BeautifulSoup(mode_buttons_html, "html.parser"))
        else:
            print("WARNING: No <body> tag found in the HTML file.")
            return False
            
        # Write the modified HTML back to the original file
        with open(report_html_path, "w", encoding="utf-8") as file:
            file.write(str(soup))
        print("✓ Injected light/dark mode buttons into report.html.")
        return True
        
    except Exception as e:
        print(f"Error injecting mode buttons: {e}")
        return False

if __name__ == "__main__":
    try:
        # Create the report QMD file
        report_qmd_path = create_report_qmd()
        
        # Render the report to HTML
        report_html_path = render_report()
        
        # Inject dark/light mode buttons
        if inject_mode_buttons(report_html_path):
            # Open the modified report in the default web browser
            webbrowser.open_new_tab('file://' + os.path.abspath(report_html_path))
            print("✓ Report opened in browser.")
        else:
            print("Warning: Mode buttons injection failed, but report was generated.")
            webbrowser.open_new_tab('file://' + os.path.abspath(report_html_path))
            
    except Exception as e:
        print(f"Error in report generation process: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)