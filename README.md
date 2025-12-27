# Thesis Flow 


**Thesis Flow** is a desktop application designed to streamline the "logic mapping" phase of writing scientific papers. It allows researchers to visually structure their arguments using a node-based system, specifically tailored for the academic workflow.

Unlike generic mind-mapping tools, ThesisFlow distinguishes between Questions, Problems, Solutions, and Explanations, and includes built-in fields for managing references per node—ensuring your bibliography aligns perfectly with your logical flow.

## 🚀 Key Features

* **Logic Tree Visualization:** Drag-and-drop canvas to map out the flow of your paper dynamically.
* **Scientific Node Types:** 4 distinct color-coded nodes for rapid identification:
    * 🟦 **Question:** Research questions, hypotheses, or objectives.
    * 🟧 **Problem:** Research gaps, issues, or challenges in current literature.
    * 🟩 **Solution:** Methodologies, proposed models, algorithms, or results.
    * ⬜ **Explanation:** Theoretical background, definitions, or analysis.
* **Reference Management:** Each node stores a specific list of references, keeping your citations organized by argument context.
* **Dynamic Linking:** Connect nodes with directional arrows to visualize the "cause and effect" or "problem and solution" relationship.
* **Lightweight:** Built with Python (Tkinter), requiring no heavy installation or external dependencies.

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **GUI Framework:** Tkinter (Standard Python Library)

## 📦 How to Run

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/DerzaAndreas/ThesisFlow.git](https://github.com/DerzaAndreas/ThesisFlow.git)
    cd ThesisFlow
    ```

2.  **Run the Application**
    Since Tkinter is included with standard Python installations, you typically do not need to install `requirements.txt`. Just run:
    ```bash
    python main.py
    ```

## 🎮 Usage Guide

1.  **Add Node:** Right-click anywhere on the canvas to select a node type (Question, Problem, Solution, Explanation).
2.  **Edit Content:** Double-click any node to open the editor. You can add the main argument text and a list of references (one per line).
3.  **Connect Arguments:** Right-click a parent node → Select **"Connect to..."** → Left-click the child node to draw a logic arrow.
4.  **Organize:** Drag nodes to rearrange your structure; connection lines will update automatically.

## 🔮 Future Roadmap

* [ ] Save & Load functionality (JSON format).
* [ ] Export tree to Image (PNG/JPG).
* [ ] Dark Mode support.

## 🤝 Contributing

Contributions are welcome! If you have ideas for features or improvements, feel free to fork the repository and submit a pull request.

## 📝 License

This project is licensed under the Apache License 2.0
