"""Reference First: local, fictional interaction simulator. Run: python app.py"""
import tkinter as tk
from tkinter import ttk
from engine import Session, CHOICES

INK = "#18383B"
PAPER = "#F5F4EE"
TEAL = "#146B62"

class App:
    def __init__(self, root):
        self.root = root
        self.session = Session()
        root.title("Reference First | Fictional evidence simulator")
        root.geometry("1160x840")
        root.minsize(900, 690)
        root.configure(bg=PAPER)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=PAPER)
        style.configure("TLabel", background=PAPER, foreground=INK, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
        style.configure("Go.TButton", background=TEAL, foreground="white")
        style.map("Go.TButton", background=[("disabled", "#D0D5D0")], foreground=[("disabled", "#4C5651")])
        outer = ttk.Frame(root, padding=22)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="REFERENCE FIRST", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Inspect the evidence. Choose the input. Then see the summary.").pack(anchor="w", pady=(2, 8))
        banner=tk.Label(outer, text="SIMULATION / FICTIONAL DATA  |  No live search or AI model  |  Not medical advice", bg="#E8D9B1", fg=INK, font=("Segoe UI",10,"bold"), padx=10, pady=8)
        banner.pack(fill="x", pady=(0,12))
        row=ttk.Frame(outer); row.pack(fill="x")
        ttk.Label(row,text="Choose a fixed case:").pack(side="left")
        self.case_ids=list(self.session.cases)
        self.case_var=tk.StringVar(value=self.session.case["title"])
        self.picker=ttk.Combobox(row,textvariable=self.case_var,values=[c["title"] for c in self.session.cases.values()],state="readonly",width=30)
        self.picker.pack(side="left",padx=10)
        self.picker.bind("<<ComboboxSelected>>",self.change_case)
        ttk.Button(row,text="Restart case",command=self.restart).pack(side="right")
        self.question=ttk.Label(outer,style="Heading.TLabel",wraplength=1080)
        self.question.pack(fill="x",pady=(12,7))
        ttk.Label(outer,text="Check the population, outcome, date and limitations. Select = input permission, not medical approval.",wraplength=1080).pack(anchor="w")
        self.notebook=ttk.Notebook(outer)
        self.notebook.pack(fill="both",expand=True,pady=10)
        self.review=ttk.Frame(self.notebook,padding=12)
        self.output=ttk.Frame(self.notebook,padding=12)
        self.notebook.add(self.review,text="1. Review sources")
        self.notebook.add(self.output,text="2. Simulated output")
        card_area=ttk.Frame(self.review); card_area.pack(fill="both",expand=True)
        self.canvas=tk.Canvas(card_area,bg=PAPER,highlightthickness=0)
        card_scroll=ttk.Scrollbar(card_area,orient="vertical",command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=card_scroll.set)
        card_scroll.pack(side="right",fill="y"); self.canvas.pack(side="left",fill="both",expand=True)
        self.cards=ttk.Frame(self.canvas)
        self.card_window=self.canvas.create_window((0,0),window=self.cards,anchor="nw")
        self.cards.bind("<Configure>",lambda event:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",self.resize_cards)
        self.inspectors=[]
        self.progress=ttk.Label(self.review,style="Heading.TLabel"); self.progress.pack(anchor="w",pady=(8,2))
        self.feedback=ttk.Label(self.review,wraplength=1040); self.feedback.pack(anchor="w",pady=(0,5))
        controls=ttk.Frame(self.review); controls.pack(fill="x")
        self.generate_button=ttk.Button(controls,text="Generate simulated summary",style="Go.TButton",command=self.generate)
        self.generate_button.pack(side="left")
        ttk.Button(controls,text="Stop without an answer",command=self.stop).pack(side="right")
        self.output_title=ttk.Label(self.output,text="No output yet",style="Heading.TLabel")
        self.output_title.pack(anchor="w")
        self.output_text=tk.Text(self.output,height=12,wrap="word",font=("Segoe UI",11),bg="white",fg=INK,relief="flat",padx=16,pady=14)
        scrollbar=ttk.Scrollbar(self.output,command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right",fill="y")
        self.output_text.pack(fill="both",expand=True,pady=8)
        self.citation_bar=ttk.Frame(self.output); self.citation_bar.pack(fill="x",pady=5)
        ttk.Button(self.output,text="Return to source review",command=lambda:self.notebook.select(0)).pack(anchor="w")
        root.bind("<Configure>",lambda event:self.question.configure(wraplength=max(400,event.width-60)) if event.widget is root else None)
        self.build_case()

    def resize_cards(self,event):
        self.canvas.itemconfigure(self.card_window,width=event.width)
        for card in self.cards.winfo_children():
            for widget in card.winfo_children():
                if isinstance(widget,ttk.Label): widget.configure(wraplength=max(360,event.width-50))

    def build_case(self):
        for window in self.inspectors:
            if window.winfo_exists(): window.destroy()
        self.inspectors=[]
        for widget in self.cards.winfo_children(): widget.destroy()
        self.question.configure(text=self.session.case["question"])
        self.choice_vars={}
        for source in self.session.case["sources"]:
            sid=source["id"]
            card=ttk.LabelFrame(self.cards,text=f"{sid}  /  {source['title']}",padding=9)
            card.pack(fill="x",pady=(0,8))
            ttk.Label(card,text=f"{source['publisher']}  |  {source['date']}",wraplength=1000).pack(anchor="w")
            ttk.Label(card,text=f"Population: {source['population']}  |  {source['design']}",wraplength=1000).pack(anchor="w",pady=(2,0))
            ttk.Label(card,text=source["passage"],wraplength=1000).pack(anchor="w",pady=5)
            row=ttk.Frame(card); row.pack(fill="x")
            ttk.Button(row,text=f"Inspect source {sid}",command=lambda s=sid:self.inspect(s)).pack(side="left",padx=(0,18))
            var=tk.StringVar(value="Unreviewed"); self.choice_vars[sid]=var
            for choice in CHOICES:
                ttk.Radiobutton(row,text=choice,value=choice,variable=var,command=lambda s=sid,v=var:self.classify(s,v.get())).pack(side="left",padx=8)
        self.set_output("No output yet", "SIMULATION / FICTIONAL DATA\n\nReview all three sources before generating a simulated summary.")
        self.feedback.configure(text="No sources are preselected. Opening a source does not classify it.")
        self.refresh()
        self.canvas.yview_moveto(0)
        self.notebook.select(0)

    def inspect(self,sid):
        source=self.session.source(sid)
        window=tk.Toplevel(self.root); window.title(f"Fictional source {sid}"); self.inspectors.append(window)
        window.geometry("710x520"); window.minsize(600,440)
        frame=ttk.Frame(window,padding=20); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text=f"{sid} / {source['title']}",style="Heading.TLabel",wraplength=550).pack(anchor="w")
        text=tk.Text(frame,height=12,wrap="word",font=("Segoe UI",11),padx=12,pady=12)
        text.pack(fill="both",expand=True,pady=10)
        body=f"FICTIONAL LOCAL SOURCE / NOT A REAL PUBLICATION\n\nPublisher: {source['publisher']}\nDate: {source['date']}\nPopulation: {source['population']}\nDesign: {source['design']}\n\nExact passage\n{source['passage']}\n\nFull local fixture\n{source['document']}\n\nRelevance note: {source['relevance']}\nLimit: {source['limit']}"
        text.insert("1.0",body); text.configure(state="disabled")
        ttk.Button(frame,text="Close source",command=window.destroy).pack(anchor="e")

    def classify(self,sid,choice):
        had_output=self.session.result is not None
        self.session.decide(sid,choice)
        invalidated=had_output and self.session.result is None
        if invalidated:
            self.set_output("Output cleared: evidence changed", "SIMULATION / FICTIONAL DATA\n\nA review choice changed. Generate again from the current selection.")
        self.feedback.configure(text=f"{sid}: {choice}."+(" Previous output cleared because the input changed." if invalidated else " You can change this choice."))
        self.refresh()

    def refresh(self):
        selected=len(self.session.selected())
        self.progress.configure(text=f"{self.session.reviewed} of {len(self.session.decisions)} sources reviewed  |  {selected} selected")
        self.generate_button.configure(state="normal" if self.session.ready else "disabled")

    def set_output(self,title,body):
        self.output_title.configure(text=title)
        self.output_text.configure(state="normal"); self.output_text.delete("1.0","end")
        self.output_text.insert("1.0",body); self.output_text.configure(state="disabled")
        for w in self.citation_bar.winfo_children(): w.destroy()

    def generate(self):
        result=self.session.generate()
        lines=["SIMULATED OUTPUT / FICTIONAL EVIDENCE", "", result["message"], ""]
        for claim in result["claims"]:
            lines += [f"[{claim['source_id']}] {claim['text']}", f"Exact passage: {claim['quote']}", f"Limit: {claim['limit']}", ""]
        lines += ["Selected input: "+(", ".join(result["input_ids"]) or "none"), "Excluded and uncertain sources are not input."]
        if result["omitted_selected_ids"]:
            lines += ["Selected but unusable in this scripted case: "+", ".join(result["omitted_selected_ids"])]
        lines += ["", "Selection is permission to use a passage, not proof of suitability. Relevance checks and disagreement detection are scripted fixture labels, not clinical judgements."]
        self.set_output(result["heading"],"\n".join(lines))
        for claim in result["claims"]:
            sid=claim["source_id"]
            ttk.Button(self.citation_bar,text=f"Inspect cited source {sid}",command=lambda s=sid:self.inspect(s)).pack(side="left",padx=(0,8))
        self.notebook.select(1)

    def change_case(self,event=None):
        index=self.picker.current()
        self.session.change_case(self.case_ids[index]); self.build_case()

    def restart(self):
        self.session.change_case(self.session.case_id); self.build_case()

    def stop(self):
        self.session.stop(); self.refresh()
        for child in self.cards.winfo_children():
            for row in child.winfo_children():
                if isinstance(row,ttk.Frame):
                    for w in row.winfo_children():
                        if isinstance(w,ttk.Radiobutton): w.configure(state="disabled")
        self.set_output("Stopped without an answer", "SIMULATION / FICTIONAL DATA\n\nYou stopped this case. No answer is generated. Restart the case or choose another case to continue.")
        self.feedback.configure(text="Stopped. Restart the case to review again.")
        self.notebook.select(1)

if __name__ == "__main__":
    root=tk.Tk(); App(root); root.mainloop()
