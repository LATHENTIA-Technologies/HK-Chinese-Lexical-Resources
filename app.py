from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, SKOS, XSD


APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "hongkong_written_chinese.json"

ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEXINFO = Namespace("http://www.lexinfo.net/ontology/3.0/lexinfo#")
HKLEX = Namespace("https://example.org/hkwc/ontology/")
RES = Namespace("https://example.org/hkwc/resource/")


st.set_page_config(
    page_title="Hong Kong Written Chinese Neologism Dictionary",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        st.error(f"Data file not found: {DATA_FILE}")
        st.stop()

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON data: {exc}")
        st.stop()


@st.cache_data
def entries_dataframe(entries: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for entry in entries:
        rows.append(
            {
                "ID": entry["id"],
                "Lemma": entry["lemma"],
                "English": entry["english"],
                "Category": entry["category"],
                "Concept": entry["concept"],
                "First attestation": entry["first_attestation"],
                "Average shift": entry["average_shift"],
                "Status": entry["status"],
            }
        )
    return pd.DataFrame(rows)


def slug(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("–", "_")
        .replace("-", "_")
    )


def build_entry_graph(entry: dict[str, Any]) -> Graph:
    graph = Graph()
    graph.bind("ontolex", ONTOLEX)
    graph.bind("lexinfo", LEXINFO)
    graph.bind("skos", SKOS)
    graph.bind("dct", DCTERMS)
    graph.bind("hklex", HKLEX)
    graph.bind("res", RES)

    entry_uri = RES[f"entry/{entry['id']}"]
    form_uri = RES[f"form/{entry['id']}"]
    sense_uri = RES[f"sense/{entry['id']}"]
    concept_uri = RES[f"concept/{slug(entry['concept'])}"]
    domain_uri = RES[f"domain/{slug(entry['category'])}"]

    graph.add((entry_uri, RDF.type, ONTOLEX.LexicalEntry))
    graph.add((entry_uri, DCTERMS.language, Literal("zh-HK")))
    graph.add((entry_uri, ONTOLEX.canonicalForm, form_uri))
    graph.add((entry_uri, ONTOLEX.sense, sense_uri))
    graph.add((entry_uri, HKLEX.identifier, Literal(entry["id"])))
    graph.add((entry_uri, HKLEX.firstAttestation, Literal(entry["first_attestation"], datatype=XSD.gYear)))
    graph.add((entry_uri, HKLEX.lastAttestation, Literal(entry["last_attestation"], datatype=XSD.gYear)))
    graph.add((entry_uri, HKLEX.averageSemanticShift, Literal(entry["average_shift"], datatype=XSD.decimal)))
    graph.add((entry_uri, HKLEX.validationStatus, Literal(entry["status"])))
    graph.add((entry_uri, HKLEX.semanticPattern, Literal(entry["semantic_pattern"])))

    graph.add((form_uri, RDF.type, ONTOLEX.Form))
    graph.add((form_uri, ONTOLEX.writtenRep, Literal(entry["lemma"], lang="zh-HK")))
    graph.add((form_uri, HKLEX.jyutping, Literal(entry["jyutping"])))

    graph.add((sense_uri, RDF.type, ONTOLEX.LexicalSense))
    graph.add((sense_uri, SKOS.definition, Literal(entry["definition"], lang="en")))
    graph.add((sense_uri, ONTOLEX.isLexicalizedSenseOf, concept_uri))

    graph.add((concept_uri, RDF.type, ONTOLEX.LexicalConcept))
    graph.add((concept_uri, SKOS.prefLabel, Literal(entry["concept"], lang="en")))
    graph.add((concept_uri, SKOS.altLabel, Literal(entry["english"], lang="en")))
    graph.add((concept_uri, SKOS.broader, domain_uri))

    graph.add((domain_uri, RDF.type, SKOS.Concept))
    graph.add((domain_uri, SKOS.prefLabel, Literal(entry["category"], lang="en")))

    return graph


def build_full_graph(entries: list[dict[str, Any]]) -> Graph:
    graph = Graph()
    for entry in entries:
        graph += build_entry_graph(entry)
    return graph


def serialize_graph(graph: Graph, rdf_format: str) -> str:
    serialized = graph.serialize(format=rdf_format)
    return serialized.decode("utf-8") if isinstance(serialized, bytes) else serialized


def render_entry_card(entry: dict[str, Any], compact: bool = False) -> None:
    st.markdown(f"## {entry['lemma']} · {entry['english']}")
    st.caption(f"{entry['id']} · Hong Kong Written Chinese · {entry['jyutping']}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Category", entry["category"])
    col2.metric("Average shift", f"{entry['average_shift']:.3f}")
    col3.metric("First attestation", entry["first_attestation"])
    col4.metric("Peak year", entry["peak_shift_year"])

    st.markdown(f"**Definition.** {entry['definition']}")
    st.markdown(f"**Semantic pattern.** {entry['semantic_pattern']}")
    st.markdown(f"**Status.** {entry['status']}")

    if compact:
        return

    st.info(f"{entry['example_zh']}\n\n{entry['example_en']}")

    shift_df = pd.DataFrame(
        {
            "Year": [int(year) for year in entry["yearly_shift"].keys()],
            "Semantic shift": list(entry["yearly_shift"].values()),
        }
    ).sort_values("Year")

    figure = px.line(
        shift_df,
        x="Year",
        y="Semantic shift",
        markers=True,
        title=f"Diachronic semantic evolution of {entry['lemma']}",
    )
    figure.update_layout(yaxis_range=[0, max(0.85, shift_df["Semantic shift"].max() + 0.1)])
    st.plotly_chart(figure, use_container_width=True)

    st.markdown("### Corpus contexts")
    for year, examples in sorted(entry["contexts"].items()):
        with st.expander(str(year)):
            for example in examples:
                st.write(f"• {example}")

    graph = build_entry_graph(entry)
    turtle = serialize_graph(graph, "turtle")

    with st.expander("OntoLex-Lemon / RDF representation"):
        st.code(turtle, language="turtle")
        st.download_button(
            "Download this entry as Turtle",
            turtle,
            file_name=f"{entry['id']}_{entry['lemma']}.ttl",
            mime="text/turtle",
            key=f"download_{entry['id']}",
        )


def navigation() -> str:
    st.sidebar.title("HKWC Dictionary")
    st.sidebar.caption("2016–2026")
    return st.sidebar.radio(
        "Navigation",
        [
            "Home",
            "Dictionary",
            "Semantic Domains",
            "Diachronic Evolution",
            "Ontology Explorer",
            "Statistics",
            "Downloads",
            "About",
        ],
    )


def page_home(project: dict[str, Any], entries: list[dict[str, Any]], categories: list[dict[str, Any]]) -> None:
    st.title(project["title"])
    st.subheader(project["subtitle"])
    st.write(
        "An interactive lexicographic prototype combining corpus-based semantic change analysis, "
        "manual validation, dictionary consultation, and OntoLex-Lemon modelling."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Corpus articles", project["corpus_articles"])
    col2.metric("Semantic candidates", project["candidate_neologisms"])
    col3.metric("Prototype entries", len(entries))
    col4.metric("Semantic domains", len(categories))

    st.markdown("### Corpus-to-ontology workflow")
    st.markdown(
        "**Corpus collection → Form-based detection → Semantic candidate refinement → "
        "Sentence-BERT modelling → Manual interpretation → Lexicographic entry → "
        "OntoLex-Lemon RDF → Interactive publication**"
    )

    st.markdown("### Featured case studies")
    featured = ["新冠", "智能", "數字", "銀行"]
    cols = st.columns(4)
    for col, lemma in zip(cols, featured):
        entry = next(item for item in entries if item["lemma"] == lemma)
        with col:
            st.markdown(f"#### {entry['lemma']}")
            st.write(entry["english"])
            st.metric("Average shift", f"{entry['average_shift']:.3f}")
            st.caption(entry["semantic_pattern"])


def page_dictionary(entries: list[dict[str, Any]]) -> None:
    st.title("Dictionary")
    st.write("Search and consult ontology-enriched lexical entries.")

    query = st.text_input("Search by Chinese lemma, English translation, definition, or concept")
    category_options = ["All"] + sorted({entry["category"] for entry in entries})
    selected_category = st.selectbox("Category", category_options)
    status_options = ["All"] + sorted({entry["status"] for entry in entries})
    selected_status = st.selectbox("Validation status", status_options)

    filtered = entries
    if query:
        lowered = query.casefold()
        filtered = [
            entry
            for entry in filtered
            if lowered in entry["lemma"].casefold()
            or lowered in entry["english"].casefold()
            or lowered in entry["definition"].casefold()
            or lowered in entry["concept"].casefold()
        ]
    if selected_category != "All":
        filtered = [entry for entry in filtered if entry["category"] == selected_category]
    if selected_status != "All":
        filtered = [entry for entry in filtered if entry["status"] == selected_status]

    st.caption(f"{len(filtered)} matching entries")
    if not filtered:
        st.warning("No entry matches the current filters.")
        return

    selected_lemma = st.selectbox("Select an entry", [entry["lemma"] for entry in filtered])
    selected_entry = next(entry for entry in filtered if entry["lemma"] == selected_lemma)
    render_entry_card(selected_entry)


def page_domains(entries: list[dict[str, Any]], categories: list[dict[str, Any]]) -> None:
    st.title("Semantic Domains")
    selected = st.selectbox("Select a semantic domain", [category["label"] for category in categories])
    category = next(category for category in categories if category["label"] == selected)
    st.write(category["description"])
    st.caption(f"Broader concept: {category['broader_concept']}")

    domain_entries = [entry for entry in entries if entry["category"] == selected]
    for entry in domain_entries:
        with st.expander(f"{entry['lemma']} · {entry['english']} · shift {entry['average_shift']:.3f}"):
            render_entry_card(entry, compact=True)


def page_evolution(entries: list[dict[str, Any]]) -> None:
    st.title("Diachronic Evolution")
    selected_lemmas = st.multiselect(
        "Compare lexical items",
        [entry["lemma"] for entry in entries],
        default=["新冠", "智能", "消費"],
    )
    if not selected_lemmas:
        st.info("Select at least one lexical item.")
        return

    records = []
    for entry in entries:
        if entry["lemma"] in selected_lemmas:
            for year, value in entry["yearly_shift"].items():
                records.append({"Lemma": entry["lemma"], "Year": int(year), "Semantic shift": value})

    df = pd.DataFrame(records)
    figure = px.line(df, x="Year", y="Semantic shift", color="Lemma", markers=True)
    figure.update_layout(yaxis_range=[0, max(0.85, df["Semantic shift"].max() + 0.1)])
    st.plotly_chart(figure, use_container_width=True)

    pivot = df.pivot_table(index="Lemma", columns="Year", values="Semantic shift", aggfunc="mean")
    heatmap = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorbar={"title": "Shift"},
            hovertemplate="Lemma: %{y}<br>Year: %{x}<br>Shift: %{z:.3f}<extra></extra>",
        )
    )
    heatmap.update_layout(title="Semantic-shift heatmap")
    st.plotly_chart(heatmap, use_container_width=True)

    st.warning(
        "Interpretation: these scores capture contextual semantic evolution. "
        "They do not automatically prove the emergence of a strict lexical semantic neologism."
    )


def page_ontology(entries: list[dict[str, Any]]) -> None:
    st.title("Ontology Explorer")
    selected_lemma = st.selectbox("Lexical entry", [entry["lemma"] for entry in entries])
    entry = next(entry for entry in entries if entry["lemma"] == selected_lemma)

    st.markdown("### Ontological path")
    st.markdown(
        f"**{entry['lemma']}** → `ontolex:LexicalEntry` → `ontolex:LexicalSense` → "
        f"**{entry['concept']}** → `skos:broader` → **{entry['category']}**"
    )

    nodes = pd.DataFrame(
        [
            {"Node": entry["lemma"], "Type": "LexicalEntry", "Relation": "ontolex:canonicalForm"},
            {"Node": entry["jyutping"], "Type": "Form", "Relation": "hklex:jyutping"},
            {"Node": entry["concept"], "Type": "LexicalConcept", "Relation": "ontolex:isLexicalizedSenseOf"},
            {"Node": entry["category"], "Type": "SKOS Concept", "Relation": "skos:broader"},
        ]
    )
    st.dataframe(nodes, use_container_width=True, hide_index=True)

    graph = build_entry_graph(entry)
    turtle = serialize_graph(graph, "turtle")
    st.code(turtle, language="turtle")


def page_statistics(entries: list[dict[str, Any]], df: pd.DataFrame) -> None:
    st.title("Statistics")

    category_counts = df.groupby("Category", as_index=False).size().rename(columns={"size": "Entries"})
    category_chart = px.bar(category_counts, x="Category", y="Entries", text="Entries", title="Entries by semantic domain")
    st.plotly_chart(category_chart, use_container_width=True)

    shift_df = df.sort_values("Average shift", ascending=False)
    shift_chart = px.bar(
        shift_df,
        x="Lemma",
        y="Average shift",
        hover_data=["English", "Category", "Status"],
        title="Average semantic-shift score by lexical item",
    )
    st.plotly_chart(shift_chart, use_container_width=True)

    st.markdown("### Top semantic-shift candidates")
    st.dataframe(
        shift_df[["Lemma", "English", "Category", "Average shift", "Status"]].head(10),
        use_container_width=True,
        hide_index=True,
    )


def page_downloads(data: dict[str, Any], entries: list[dict[str, Any]], df: pd.DataFrame) -> None:
    st.title("Downloads")
    st.write("Export the prototype lexical resource in interoperable formats.")

    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    csv_text = df.to_csv(index=False)
    graph = build_full_graph(entries)
    turtle = serialize_graph(graph, "turtle")
    rdf_xml = serialize_graph(graph, "xml")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download JSON", json_text, "hongkong_written_chinese.json", "application/json")
        st.download_button("Download CSV", csv_text, "hongkong_written_chinese.csv", "text/csv")
    with col2:
        st.download_button("Download Turtle RDF", turtle, "hongkong_written_chinese.ttl", "text/turtle")
        st.download_button("Download RDF/XML", rdf_xml, "hongkong_written_chinese.rdf", "application/rdf+xml")

    st.markdown("### RDF preview")
    st.code("\n".join(turtle.splitlines()[:80]), language="turtle")


def page_about(project: dict[str, Any]) -> None:
    st.title("About")
    st.markdown(
        f"""
This prototype presents a corpus-to-ontology workflow for **{project['language']}** over the period
**{project['period']}**. It supports dictionary consultation, semantic-domain browsing, diachronic
visualization, and export in OntoLex-Lemon-compatible RDF.

The current entries are a research prototype built from selected case studies. Average semantic-shift
scores and yearly values should be replaced by the definitive outputs of the corpus-analysis pipeline
before publication.

**Methodological principle:** the system identifies candidates for contextual semantic evolution.
A high shift score may reflect lexical semantic change, semantic expansion, topic change, or discourse change.
Expert annotation and a gold-standard dataset are therefore necessary for quantitative evaluation.
        """
    )


def main() -> None:
    data = load_data()
    project = data["project"]
    categories = data["categories"]
    entries = data["entries"]
    df = entries_dataframe(entries)

    page = navigation()

    if page == "Home":
        page_home(project, entries, categories)
    elif page == "Dictionary":
        page_dictionary(entries)
    elif page == "Semantic Domains":
        page_domains(entries, categories)
    elif page == "Diachronic Evolution":
        page_evolution(entries)
    elif page == "Ontology Explorer":
        page_ontology(entries)
    elif page == "Statistics":
        page_statistics(entries, df)
    elif page == "Downloads":
        page_downloads(data, entries, df)
    elif page == "About":
        page_about(project)


if __name__ == "__main__":
    main()
#cd hk_lexicon_app
#pip install -r requirements.txt
#streamlit run app.py