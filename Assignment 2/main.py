import networkx as nx
import random
import random
import time
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
# Step 1: Load Facebook Graph
print("Loading graph...")

G = nx.read_edgelist("facebook_combined.txt", nodetype=int)

print("Graph loaded!")
print("Number of nodes:", G.number_of_nodes())
print("Number of edges:", G.number_of_edges())
import pandas as pd

print("\nCalculating graph features...")

# Degree
degree = dict(G.degree())

# Clustering Coefficient
clustering = nx.clustering(G)

# Betweenness Centrality
betweenness = nx.betweenness_centrality(G, k=500)   

# Create DataFrame of features
df = pd.DataFrame({
    "node": list(G.nodes()),
    "degree": [degree[n] for n in G.nodes()],
    "clustering": [clustering[n] for n in G.nodes()],
    "betweenness": [betweenness[n] for n in G.nodes()]
})



print("\nAssigning labels (bots/humans)...")

# Choose 5% of nodes as bots
num_bots = int(0.05 * G.number_of_nodes())
bots = set(random.sample(list(G.nodes()), num_bots))

# Create label for each node
df["label"] = df["node"].apply(lambda n: 1 if n in bots else 0)


print(df['label'].value_counts())



X = df[["degree", "clustering", "betweenness"]]   # input features
y = df["label"]                                    # target (bot/human)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)


print("\nTraining baseline bot detection model...")

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\nBaseline Model Performance:")
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))



########Structural Evasion Attack########
print("\nApplying Structural Evasion Attack...")

G_evasion = G.copy()

for b in bots:
    neighbors = list(G_evasion.neighbors(b))

    for n in neighbors[:3]:
        G_evasion.remove_edge(b, n)

print("Structural Evasion Attack applied!")
print("\nRecalculating features after Structural Evasion...")

degree_e = dict(G_evasion.degree())
clustering_e = nx.clustering(G_evasion)
betweenness_e = nx.betweenness_centrality(G_evasion, k=500)

df_e = pd.DataFrame({
    "node": list(G_evasion.nodes()),
    "degree": [degree_e[n] for n in G_evasion.nodes()],
    "clustering": [clustering_e[n] for n in G_evasion.nodes()],
    "betweenness": [betweenness_e[n] for n in G_evasion.nodes()],
    "label": df["label"]  
})
print("\nEvaluating model after Structural Evasion...")

X_e = df_e[["degree", "clustering", "betweenness"]]
y_e = df_e["label"]

X_train_e, X_test_e, y_train_e, y_test_e = train_test_split(
    X_e, y_e, test_size=0.3, random_state=42, stratify=y_e
)

model_e = RandomForestClassifier(n_estimators=200, random_state=42)
model_e.fit(X_train_e, y_train_e)
y_pred_e = model_e.predict(X_test_e)

print("Performance After Structural Evasion:")
print("Accuracy:", accuracy_score(y_test_e, y_pred_e))
print(classification_report(y_test_e, y_pred_e))



########Poisoning Attack########

print("\nApplying Graph Poisoning Attack (robust)...")

# Copy original graph
G_poison = G.copy()

# Create a labels dict from existing df for robustness (node -> label)
labels_dict = {row['node']: row['label'] for _, row in df.iterrows()}

# Add fake nodes
num_fake = 30
fake_nodes = [f"fake_{i}" for i in range(num_fake)]

for f in fake_nodes:
    G_poison.add_node(f)
    # connect the fake node to 3 random real nodes
    for _ in range(3):
        target = random.choice(list(G.nodes()))
        G_poison.add_edge(f, target)
    # mark fake nodes as humans (poisoning: wrong label)
    labels_dict[f] = 0

print("Fake nodes added:", len(fake_nodes))
print("Total nodes after poisoning:", G_poison.number_of_nodes())

# Recalculate features (degree, clustering, betweenness)
print("\nRecalculating features after Graph Poisoning...")
t0 = time.time()

degree_p = dict(G_poison.degree())
clustering_p = nx.clustering(G_poison)

# Use approximated betweenness with k to speed up; choose k smaller if too slow
betweenness_p = nx.betweenness_centrality(G_poison, k=300, seed=42)

t1 = time.time()
print(f"Feature calc done in {t1-t0:.1f}s")

# Build DataFrame robustly: for each node in G_poison, fetch label from labels_dict
nodes_p = list(G_poison.nodes())
labels_for_df = [labels_dict.get(n, 0) for n in nodes_p]  # default 0 if missing

df_p = pd.DataFrame({
    "node": nodes_p,
    "degree": [degree_p[n] for n in nodes_p],
    "clustering": [clustering_p[n] for n in nodes_p],
    "betweenness": [betweenness_p[n] for n in nodes_p],
    "label": labels_for_df
})

print("df_p created. Shape:", df_p.shape)
print(df_p.head())

# ---- Retrain model after poisoning ----
print("\nEvaluating model after Graph Poisoning...")

X_p = df_p[["degree", "clustering", "betweenness"]]
y_p = df_p["label"]



X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(
    X_p, y_p, test_size=0.3, random_state=42, stratify=y_p
)

model_p = RandomForestClassifier(n_estimators=200, random_state=42)
model_p.fit(X_train_p, y_train_p)
y_pred_p = model_p.predict(X_test_p)

print("Performance After Graph Poisoning:")
print("Accuracy:", accuracy_score(y_test_p, y_pred_p))
print(classification_report(y_test_p, y_pred_p))

# ---- Visualizations ----

plt.figure(figsize=(8,6))
nx.draw_spring(G, node_size=10)
plt.title("Original Graph")
plt.savefig("original_graph.png")
plt.show()

plt.figure(figsize=(8,6))
nx.draw_spring(G_evasion, node_size=10)
plt.title("After Structural Evasion")
plt.savefig("evasion_graph.png")
plt.show()

plt.figure(figsize=(8,6))
nx.draw_spring(G_poison, node_size=10)
plt.title("After Graph Poisoning")
plt.savefig("poison_graph.png")
plt.show()
