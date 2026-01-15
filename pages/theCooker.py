import streamlit as st
import json
from collections import defaultdict

JSON_PATH = r"data/arcraiders_items.json"

# ---------------------------------------------------------
# Carregar JSON limpo
# ---------------------------------------------------------

@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_json(JSON_PATH)

st.set_page_config(page_title="The Cooker 4.1", page_icon="🔥", layout="wide")
st.title("🔥 The Cooker 4.1 — Crafting & Planning")

# ---------------------------------------------------------
# Converter JSON limpo → receitas simples
# ---------------------------------------------------------

def extract_all_recipes(clean_data):
    recipes = {}

    for item_name, info in clean_data.items():

        # receita base
        if info.get("recipe"):
            recipes[item_name] = {
                "produces": 1,
                "ingredients": info["recipe"]
            }

        # versões
        for version, vdata in info.get("versions", {}).items():
            full_name = f"{item_name} {version}"
            recipes[full_name] = {
                "produces": 1,
                "ingredients": vdata.get("ingredients", {})
            }

    return recipes

recipes = extract_all_recipes(data)

# Lista de ingredientes únicos
all_ingredients = sorted({ing for r in recipes.values() for ing in r["ingredients"]})

# ---------------------------------------------------------
# Inventário do usuário (no corpo principal)
# ---------------------------------------------------------

st.header("🧺 Inventário")

if "inventory" not in st.session_state:
    st.session_state.inventory = {}

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    ing = st.selectbox("Ingrediente", all_ingredients, key="inv_ing")

with col2:
    qty = st.number_input("Quantidade", min_value=1, step=1, key="inv_qty")

with col3:
    st.write("")  # espaçamento
    if st.button("Adicionar ao inventário"):
        st.session_state.inventory[ing] = st.session_state.inventory.get(ing, 0) + qty

# tabela sempre visível
st.subheader("📦 Itens no inventário")

if st.session_state.inventory:
    edit_cols = st.columns([4, 2, 2, 2])

    edit_cols[0].write("**Ingrediente**")
    edit_cols[1].write("**Quantidade**")
    edit_cols[2].write("**Alterar**")
    edit_cols[3].write("**Remover**")

    to_delete = None

    for i, (item, amount) in enumerate(st.session_state.inventory.items()):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])

        c1.write(item)
        new_amount = c2.number_input(
            f"qty_{i}", min_value=0, value=amount, step=1, label_visibility="collapsed"
        )

        if new_amount != amount:
            st.session_state.inventory[item] = new_amount

        if c4.button("❌", key=f"del_{i}"):
            to_delete = item

    if to_delete:
        del st.session_state.inventory[to_delete]

else:
    st.info("Nenhum ingrediente adicionado ainda.")

if st.button("Limpar inventário"):
    st.session_state.inventory = {}

inventory = st.session_state.inventory

# ---------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------

def can_craft(ingredients, inventory):
    for ing, req in ingredients.items():
        if inventory.get(ing, 0) < req:
            return False
    return True

def calculate_crafting(recipes, inventory):
    results = []

    for item, recipe in recipes.items():
        max_units = float("inf")

        for ing, req_qty in recipe["ingredients"].items():
            have = inventory.get(ing, 0)
            if have < req_qty:
                max_units = 0
                break
            max_units = min(max_units, have // req_qty)

        if max_units > 0:
            total_cost = sum(recipe["ingredients"].values())
            results.append({
                "Item": item,
                "Máx. Unidades": max_units,
                "Custo Total (ingredientes)": total_cost,
                "Ingredientes": recipe["ingredients"]
            })

    return results

def calculate_shopping_list(recipes, target_item, target_qty, inventory):
    if target_item not in recipes:
        return None

    recipe = recipes[target_item]
    needed = {}

    for ing, req_qty in recipe["ingredients"].items():
        total_needed = req_qty * target_qty
        have = inventory.get(ing, 0)
        missing = max(total_needed - have, 0)

        needed[ing] = {
            "Necessário": total_needed,
            "Você tem": have,
            "Falta": missing
        }

    return needed

def calculate_efficiency(recipes):
    eff = []
    for item, recipe in recipes.items():
        total_ing = sum(recipe["ingredients"].values())
        eff.append({
            "Item": item,
            "Total de Ingredientes": total_ing
        })
    eff.sort(key=lambda x: x["Total de Ingredientes"])
    return eff

# ---------------------------------------------------------
# Árvore de crafting recursiva + custo total
# ---------------------------------------------------------

def expand_crafting_tree(item, qty, recipes, depth=0, visited=None):
    if visited is None:
        visited = set()

    tree = []
    base_needs = defaultdict(int)

    tree.append({"item": item, "qty": qty, "depth": depth})

    if item not in recipes or item in visited:
        base_needs[item] += qty
        return tree, base_needs

    visited.add(item)
    recipe = recipes[item]

    for ing, req_qty in recipe["ingredients"].items():
        total_needed = req_qty * qty
        subtree, subbase = expand_crafting_tree(ing, total_needed, recipes, depth + 1, visited)
        tree.extend(subtree)
        for b, q in subbase.items():
            base_needs[b] += q

    visited.remove(item)
    return tree, base_needs

# ---------------------------------------------------------
# Simulador de upgrades
# ---------------------------------------------------------

def get_item_versions(item_base, recipes):
    versions = []
    for name in recipes.keys():
        if name.startswith(item_base + " "):
            versions.append(name)
    versions.sort()
    return versions

def simulate_upgrade_path(item_base, target_version, recipes):
    versions = get_item_versions(item_base, recipes)
    if target_version not in versions:
        return []

    path = []
    ordered = versions

    for i in range(len(ordered) - 1):
        frm = ordered[i]
        to = ordered[i + 1]
        path.append((frm, to))

    final_path = []
    for frm, to in path:
        final_path.append((frm, to))
        if to == target_version:
            break

    steps = []
    for frm, to in final_path:
        rec = recipes[to]
        steps.append({
            "from": frm,
            "to": to,
            "ingredients": rec["ingredients"]
        })

    return steps

# ---------------------------------------------------------
# Layout principal: abas
# ---------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 O que posso fabricar",
    "🧾 Lista de compras",
    "🌳 Árvore de crafting",
    "⬆️ Simulador de upgrades"
])

# ---------------------------------------------------------
# TAB 1 — O que posso fabricar
# ---------------------------------------------------------

with tab1:
    st.header("🔍 O que posso fabricar")

    if st.button("Calcular o que posso fabricar"):
        results = calculate_crafting(recipes, inventory)

        if not results:
            st.warning("Você não pode fabricar nada com os ingredientes fornecidos.")
        else:
            st.success("Itens que você pode fabricar:")
            table_rows = []
            for r in results:
                table_rows.append({
                    "Item": r["Item"],
                    "Máx. Unidades": r["Máx. Unidades"],
                    "Custo Total (ingredientes)": r["Custo Total (ingredientes)"]
                })
            st.table(table_rows)

            with st.expander("Ver detalhes das receitas"):
                st.json(results)

# ---------------------------------------------------------
# TAB 2 — Lista de compras
# ---------------------------------------------------------

with tab2:
    st.header("🧾 Lista de compras para um item")

    target_item = st.selectbox("Escolha o item alvo", sorted(recipes.keys()), key="shop_item")
    target_qty = st.number_input("Quantidade desejada", min_value=1, step=1, key="shop_qty")

    if st.button("Calcular lista de compras"):
        shopping = calculate_shopping_list(recipes, target_item, target_qty, inventory)

        if shopping is None:
            st.error("Item não encontrado nas receitas.")
        else:
            st.subheader(f"Lista de compras para {target_qty}× {target_item}")
            rows = []
            for ing, info in shopping.items():
                rows.append({
                    "Ingrediente": ing,
                    "Necessário": info["Necessário"],
                    "Você tem": info["Você tem"],
                    "Falta": info["Falta"]
                })
            st.table(rows)

# ---------------------------------------------------------
# TAB 3 — Árvore de crafting
# ---------------------------------------------------------

with tab3:
    st.header("🌳 Árvore de crafting e custo total")

    target_item_tree = st.selectbox("Escolha o item alvo", sorted(recipes.keys()), key="tree_item")
    target_qty_tree = st.number_input("Quantidade desejada", min_value=1, step=1, key="tree_qty")

    if st.button("Gerar árvore de crafting"):
        tree, base_needs = expand_crafting_tree(target_item_tree, target_qty_tree, recipes)

        st.subheader("Estrutura de crafting")
        rows = []
        for node in tree:
            rows.append({
                "Item": ("  " * node["depth"]) + node["item"],
                "Quantidade": node["qty"]
            })
        st.table(rows)

        st.subheader("Materiais básicos necessários (sem receita)")
        base_rows = []
        for ing, q in base_needs.items():
            have = inventory.get(ing, 0)
            base_rows.append({
                "Ingrediente": ing,
                "Necessário": q,
                "Você tem": have,
                "Falta": max(q - have, 0)
            })
        st.table(base_rows)

# ---------------------------------------------------------
# TAB 4 — Simulador de upgrades
# ---------------------------------------------------------

with tab4:
    st.header("⬆️ Simulador de upgrades")

    base_items = sorted(data.keys())
    base_choice = st.selectbox("Escolha o item base (ex: Kettle)", base_items, key="upgrade_base")

    versions = get_item_versions(base_choice, recipes)
    if not versions:
        st.info("Este item não possui versões registradas no banco de dados.")
    else:
        target_version = st.selectbox("Versão alvo", versions, key="upgrade_target")

        if st.button("Simular caminho de upgrade"):
            steps = simulate_upgrade_path(base_choice, target_version, recipes)

            if not steps:
                st.warning("Não foi possível montar o caminho de upgrade.")
            else:
                st.subheader("Passos de upgrade")
                rows = []
                for s in steps:
                    rows.append({
                        "De": s["from"],
                        "Para": s["to"],
                        "Ingredientes": ", ".join(f"{v}x {k}" for k, v in s["ingredients"].items())
                    })
                st.table(rows)

                total_needs = defaultdict(int)
                for s in steps:
                    for ing, q in s["ingredients"].items():
                        total_needs[ing] += q

                st.subheader("Custo total direto de upgrade (sem expandir crafting)")
                total_rows = []
                for ing, q in total_needs.items():
                    have = inventory.get(ing, 0)
                    total_rows.append({
                        "Ingrediente": ing,
                        "Necessário": q,
                        "Você tem": have,
                        "Falta": max(q - have, 0)
                    })
                st.table(total_rows)
