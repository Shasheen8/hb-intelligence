import json

def render_html():
    try:
        with open('intel/cybersecurity_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: cybersecurity_data.json not found")
        return

    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>HealthyByte Intelligence Dashboard</title>
      <style>
        body {
          font-family: 'Helvetica Neue', Arial, sans-serif;
          background: #f4f7fa;
          margin: 0;
          padding: 0;
        }
        .container {
          max-width: 900px;
          margin: 0 auto;
          padding: 40px 20px;
        }
        h1 {
          text-align: center;
          color: #1a73e8;
          font-size: 2.5em;
          margin-bottom: 10px;
        }
        .intro {
          text-align: center;
          color: #4a5568;
          font-size: 1.2em;
          max-width: 700px;
          margin: 0 auto 40px;
          line-height: 1.6;
        }
        .intro strong {
          color: #1a73e8;
        }
        h2 {
          color: #2d3748;
          font-size: 1.8em;
          margin: 40px 0 20px;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 10px;
        }
        ul {
          list-style: none;
          padding: 0;
        }
        li {
          background: #fff;
          margin-bottom: 20px;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: transform 0.2s;
        }
        li:hover {
          transform: translateY(-5px);
        }
        h3 {
          margin: 0;
          font-size: 1.3em;
        }
        h3 a {
          color: #1a73e8;
          text-decoration: none;
        }
        h3 a:hover {
          text-decoration: underline;
        }
        .meta {
          color: #718096;
          font-size: 0.9em;
          margin: 5px 0;
        }
        .summary {
          color: #4a5568;
          margin: 10px 0 0;
          line-height: 1.5;
        }
        @media (max-width: 600px) {
          .container {
            padding: 20px 10px;
          }
          h1 {
            font-size: 2em;
          }
          h2 {
            font-size: 1.5em;
          }
          .intro {
            font-size: 1em;
          }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>HealthyByte Intelligence Dashboard</h1>
        <div class="intro">
          Welcome to your <strong>security command center</strong>! Dive into the latest news, tools, vulnerabilities, and events shaking up the security world. From sneaky malware to game-changing tech, it's got it all—<strong>updated weekly</strong> to keep you ahead of the curve. Stay sharp, stay secure!
        </div>
    '''
    for category in ['Cybersecurity Business', 'Security Tools', 'Threats and Vulnerabilities', 'Cyber Events']:
        html += f'<h2>{category}</h2><ul>'
        items = data.get(category, [])
        if not items:
            html += '<li class="summary">No items available</li>'
        for item in items:
            html += f'''
            <li>
              <h3><a href="{item["link"]}" target="_blank">{item["title"]}</a></h3>
              <p class="meta">{item["source"]} • {item["published"][:10]}</p>
              <p class="summary">{item["summary"]}</p>
            </li>
            '''
        html += '</ul>'
    html += '''
      </div>
    </body>
    </html>
    '''

    with open('intel/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Generated intel/dashboard.html")

if __name__ == "__main__":
    render_html()