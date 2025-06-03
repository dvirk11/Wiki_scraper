def generate_html(mapping, output_path="output.html"):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Animal Collateral Adjectives</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
            background: white;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 12px;
            vertical-align: top;
        }
        th {
            background-color: #e0e0e0;
        }
        td.adjective {
            width: 30%;
            font-weight: bold;
            background-color: #fafafa;
        }
        td.animals {
            width: 70%;
        }
        .animal-entry {
            margin-bottom: 20px;
        }
        .animal-entry img {
            max-width: 200px;
            max-height: 200px;
            margin-top: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        a {
            text-decoration: none;
            color: #0645ad;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Animal Collateral Adjectives</h1>
    <table>
        <thead>
            <tr>
                <th>Collateral Adjective</th>
                <th>Animals</th>
            </tr>
        </thead>
        <tbody>
    """

    for adjective, animals in sorted(mapping.items()):
        animal_html = ""
        for entry in animals:
            name = entry["name"]
            wiki_url = entry.get("wiki_url", "#")
            image_path = entry.get("local_image", "")
            img_html = f'<img src="{image_path}" alt="{name}">' if image_path else ""
            animal_html += f"""
            <div class="animal-entry">
                <a href="{wiki_url}" target="_blank">{name}</a><br>
                {img_html}
            </div>
            """

        html += f"""
        <tr>
            <td class="adjective">{adjective}</td>
            <td class="animals">{animal_html}</td>
        </tr>
        """

    html += """
        </tbody>
    </table>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML file written to: {output_path}")
    return output_path
