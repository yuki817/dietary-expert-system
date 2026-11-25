# **Project Requirements & Specification: Multi-Standard Dietary & Supply Chain Compliance Expert System**

# **1\. Project Overview & Objectives**

## **1.1 System Name & Context**

**System Name:** Multi-Standard Dietary & Supply Chain Compliance Expert System

Globalized food manufacturing relies on deeply nested supply chains where raw ingredients undergo multi-tiered processing across various international suppliers. Determining whether a final consumer product satisfies complex, multi-jurisdictional dietary standards (e.g., Halal, Kosher, Vegetarian, Vegan, Allergen-Free) requires traversing sub-ingredient trees down to primary biological origins, processing aids, and certification verifications. Traditional relational systems fail to efficiently perform multi-level transitive dependency tracing and deterministic rule-based inference across overlapping regulatory contexts.

## **1.2 Core Goal**

The core goal of this project is to construct a Knowledge Graph (KG) based expert system that evaluates finished food products and their complex supply chains simultaneously against multiple dietary and regulatory frameworks. Using semantic Web standards, declarative SPARQL CONSTRUCT rules, and graph-traversal algorithms, the system automatically infers compliance status (Pass, Audit Required, Non-Compliant), identifies deep-tier violations, and recommends suitable functional ingredient substitutions.

## **1.3 Team Size & Timeline**

- **Team Size:** 3-person agile engineering team.
- **Sprint Duration:** 3-day agile sprint.

## **1.4 Core Assignment Deliverables**

1. **Ontology Schema (T-Box):** Formal OWL/RDFS domain model capturing products, nested ingredients, origins, functional roles, certifications, and compliance issues.
2. **Declarative Reasoning Rules:** Deterministic SPARQL CONSTRUCT and OWL-RDFS rule sets for dynamic compliance inference and substitution matching.
3. **Instantiated Knowledge Graph (A-Box):** Comprehensive dataset comprising multi-nested product trees, raw materials, E-numbers, ethanol thresholds, and third-party certificates.
4. **Interactive Use-Cases:** Minimum three functional UI modules evaluating multi-standard compliance, visual supply chain graph traversal, and automated ingredient reformulation.
5. **Source Code & Live Deployment:** Fully documented, public GitHub repository integrated with automated continuous deployment to Streamlit Community Cloud.
6. **Technical Documentation:** Final Technical Report published in PDF format (.pdf) detailing architectural design, evaluation results, and live system links.

---

# **2\. System Architecture & Technology Stack**

To ensure rapid execution during a 3-day sprint and eliminate runtime overhead associated with JVM-based triple stores, the system adopts a pure-Python Semantic Web architecture. This stack guarantees lightweight cloud deployment, fast execution of SPARQL CONSTRUCT queries in memory, and seamless integration with web-based graph visualization libraries.

```
+-----------------------------------------------------------------------------------+

|                                 USER INTERFACE                                    |
|---|
+-----------------------------------------------------------------------------------+
                                          |
                                    SPARQL Queries
                                          v
+-----------------------------------------------------------------------------------+
|                              PYTHON INFERENCE ENGINE                              |
|                              (rdflib In-Memory Engine)                            |
|  +---------------------------------+  +----------------------------------------+  |
|  |     T-Box & A-Box Parsing       |  |       SPARQL CONSTRUCT Rules           |  |
|  |   (OWL / RDFS Turtle Schema)    |  |  (Halal, Kosher, Vegan, Substitutions) |  |
|  +---------------------------------+  +----------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                          |
                                    Version Control
                                          v
+-----------------------------------------------------------------------------------+
|                           DEPLOYMENT & INFRASTRUCTURE                             |
|                    GitHub Repository + Streamlit Community Cloud                  |
+-----------------------------------------------------------------------------------+
```

## **2.1 Technology Stack Components**

- **Ontology Engineering:** Protégé 5.x for formal T-Box modeling, serialized as Turtle (`.ttl`).
- **Knowledge Graph & Inference Engine:** Python `rdflib` (v6.x+) for parsing RDF graphs, executing deterministic SPARQL CONSTRUCT rule sets, and manipulating graph models in memory.
- **Frontend & Graph Visualization:** Streamlit for interactive dashboard rendering, coupled with `streamlit-agraph` for real-time node-edge network visualization of supply chain hierarchies.
- **Version Control & Cloud Hosting:** GitHub for codebase versioning and Streamlit Community Cloud for automated, zero-JVM serverless deployment.

---

# **3\. Ontology Specification (T-Box)**

**Namespace Prefix:** `food: <http://example.org/food-compliance#>`

## **3.1 Domain Classes**

| Class Name         | Superclass  | Description                                                                                                                                                                                                                 |
| :----------------- | :---------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FoodProduct`      | `owl:Thing` | Finished consumer goods made of multiple ingredients (e.g., Instant Ramen, Gummy Candy).                                                                                                                                    |
| `Ingredient`       | `owl:Thing` | Raw materials, sub-ingredients, processing aids, and E-number additives (e.g., Gelatin, Whey, E471).                                                                                                                        |
| `BiologicalOrigin` | `owl:Thing` | Taxonomic source classification powering origin tracing. Subclasses: `PlantOrigin`, `AnimalOrigin`, `MicrobialOrigin`, `SyntheticOrigin`. Subclasses of `AnimalOrigin`: `Porcine`, `Bovine`, `Poultry`, `Marine`, `Insect`. |
| `AnimalByproduct`  | `owl:Thing` | Non-meat animal derivatives. Subclasses: `Dairy`, `Egg`, `Honey`, `AnimalFat`, `AnimalEnzyme`, `MeatTissue`.                                                                                                                |
| `Certificate`      | `owl:Thing` | Third-party compliance verifications. Subclasses: `HalalCert`, `KosherCert`.                                                                                                                                                |
| `DietaryStandard`  | `owl:Thing` | Target regulatory or dietary frameworks. Instances: `Halal`, `Kosher`, `Vegetarian`, `Vegan`, `AllergenFree`.                                                                                                               |
| `FunctionalRole`   | `owl:Thing` | Chemical/culinary purpose of an ingredient (e.g., `GellingAgent`, `Emulsifier`, `DoughConditioner`, `Flavoring`).                                                                                                           |
| `ComplianceIssue`  | `owl:Thing` | Diagnostic node generated by inference rules detailing standard violations or audit requirements.                                                                                                                           |

## **3.2 Object & Data Properties**

| Property Name        | Type           | Domain \$\\rightarrow\$ Range                                 | Characteristics / Notes                                                                |
| :------------------- | :------------- | :------------------------------------------------------------ | :------------------------------------------------------------------------------------- |
| `containsIngredient` | ObjectProperty | `FoodProduct / Ingredient $\rightarrow$ Ingredient`           | `owl:TransitiveProperty`. Enables multi-level BOM sub-ingredient tracing.              |
| `derivedFrom`        | ObjectProperty | `Ingredient $\rightarrow$ BiologicalOrigin / AnimalByproduct` | Connects an ingredient directly to its biological or animal source.                    |
| `hasCertificate`     | ObjectProperty | `Ingredient $\rightarrow$ Certificate`                        | Links an ingredient or derivative to a valid third-party certificate.                  |
| `hasFunctionalRole`  | ObjectProperty | `Ingredient $\rightarrow$ FunctionalRole`                     | Categorizes an ingredient by purpose to enable alternative matching.                   |
| `ethanolPercentage`  | DataProperty   | `Ingredient $\rightarrow$ xsd:float`                          | Represents ethanol concentration by volume for Halal compliance.                       |
| `isCompliantWith`    | ObjectProperty | `FoodProduct $\rightarrow$ DietaryStandard`                   | \[Inferred\] Indicates that a product fully satisfies a dietary standard.              |
| `isNonCompliantWith` | ObjectProperty | `FoodProduct $\rightarrow$ DietaryStandard`                   | \[Inferred\] Indicates a direct violation of a dietary standard.                       |
| `requiresAuditFor`   | ObjectProperty | `FoodProduct $\rightarrow$ DietaryStandard`                   | \[Inferred\] Indicates missing certification on a conditionally acceptable ingredient. |
| `hasIssue`           | ObjectProperty | `FoodProduct $\rightarrow$ ComplianceIssue`                   | \[Inferred\] Connects a product to a specific generated compliance issue report node.  |

---

# **4\. Declarative Reasoning Rules Specification**

Compliance rules are expressed deterministically via SPARQL CONSTRUCT queries. These queries evaluate the graph, assert inferred relationships (isNonCompliantWith, requiresAuditFor, isCompliantWith), and generate structured ComplianceIssue instances.

## **4.1 Rule Set A: Halal Compliance Framework**

- **Haram Inference Rule (Non-Compliant):** A product is non-compliant with Halal if it transitively contains any ingredient derived from `Porcine` or `Insect` (e.g., Carmine E120), or if any ingredient has an `ethanolPercentage` exceeding 0.5%.

l  
PREFIX food: [http\://example.org/food-compliance\#](http://example.org/food-compliance#)  
PREFIX rdfs: [http\://www\.w3.org/2000/01/rdf-schema\#](http://www.w3.org/2000/01/rdf-schema#)

CONSTRUCT {  
?product food:isNonCompliantWith food:Halal ;  
food:hasIssue ?issue .  
?issue a food:ComplianceIssue ;  
rdfs:label ?issueText ;  
food:flaggedIngredient ?ingredient .  
}  
WHERE {  
?product food:containsIngredient+ ?ingredient .  
{  
?ingredient food:derivedFrom ?source .  
?source a ?sourceType .  
FILTER(?sourceType IN (food:Porcine, food:Insect))  
BIND(CONCAT("Haram ingredient detected: ", STR(?ingredient), " derived from forbidden origin.") AS ?issueText)  
} UNION {  
?ingredient food:ethanolPercentage ?alc .  
FILTER(?alc \> 0.5)  
BIND(CONCAT("Halal limit exceeded: ", STR(?ingredient), " contains ", STR(?alc), "% ethanol.") AS ?issueText)  
}  
BIND(IRI(CONCAT("http\://example.org/issue/halal-fail-", STRUUID())) AS ?issue)  
}

````

* **Mashbooh Inference Rule (Audit Required):** A product requires a Halal audit if it contains ingredients derived from `Bovine`, `Poultry`, or `AnimalEnzyme` that lack a linked `HalalCert`.

```sparql
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?product food:requiresAuditFor food:Halal ;
           food:hasIssue ?issue .
  ?issue a food:ComplianceIssue ;
         rdfs:label ?issueText ;
         food:flaggedIngredient ?ingredient .
}
WHERE {
  ?product food:containsIngredient+ ?ingredient .
  ?ingredient food:derivedFrom ?source .
  ?source a ?sourceType .
  FILTER(?sourceType IN (food:Bovine, food:Poultry, food:AnimalEnzyme))
  FILTER NOT EXISTS { ?ingredient food:hasCertificate ?cert . ?cert a food:HalalCert . }

  BIND(CONCAT("Audit required (Mashbooh): ", STR(?ingredient), " requires valid Halal certification.") AS ?issueText)
  BIND(IRI(CONCAT("http://example.org/issue/halal-audit-", STRUUID())) AS ?issue)
}
````

## **4.2 Rule Set B: Kosher Compliance Framework**

- **Treif Inference Rule (Non-Compliant):** A product is non-compliant with Kosher if it transitively contains ingredients derived from `Porcine` or `Marine` (shellfish), or if animal/processed derivatives lack a valid `KosherCert`.
- **Basar BeChalav Rule (Meat-Dairy Co-occurrence):** A product is marked non-compliant with Kosher if it transitively contains both meat derivatives (`MeatTissue`, `Bovine`, `Poultry`) and dairy derivatives (`Dairy`, `Whey`, `Casein`, `Cheese`).

```
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?product food:isNonCompliantWith food:Kosher ;
           food:hasIssue ?issue .
  ?issue a food:ComplianceIssue ;
         rdfs:label "Kosher violation: Mixing meat and dairy derivatives (Basar BeChalav)." .
}
WHERE {
  ?product food:containsIngredient+ ?ing1, ?ing2 .
  ?ing1 food:derivedFrom ?src1 .
  ?ing2 food:derivedFrom ?src2 .

  ?src1 a ?type1 . FILTER(?type1 IN (food:MeatTissue, food:Bovine, food:Poultry))
  ?src2 a ?type2 . FILTER(?type2 IN (food:Dairy, food:Whey, food:Casein))

  BIND(IRI(CONCAT("http://example.org/issue/kosher-meatdairy-", STRUUID())) AS ?issue)
}
```

## **4.3 Rule Set C: Vegetarian & Vegan Compliance Framework**

- **Non-Vegetarian Rule:** Flag products containing `MeatTissue`, `AnimalFat`, or `AnimalEnzyme` (e.g., animal rennet).
- **Non-Vegan Rule:** Flag products failing Vegetarian criteria OR containing any `AnimalByproduct` (`Dairy`, `Egg`, `Honey`).

## **4.4 Rule Set D: Ingredient Substitution Inference Rule**

Identifies suitable substitute candidates for non-compliant ingredients by matching the flagged ingredient's `FunctionalRole` with alternative ingredients in the A-Box that satisfy all target `DietaryStandard` requirements.

```
PREFIX food: <http://example.org/food-compliance#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?flaggedIng food:hasSuggestedSubstitute ?substitute .
}
WHERE {
  ?flaggedIng food:hasFunctionalRole ?role .
  ?substitute food:hasFunctionalRole ?role .
  FILTER(?flaggedIng != ?substitute)

  -- Ensure substitute is plant/microbial/synthetic and lacks offending traits
  ?substitute food:derivedFrom ?subSource .
  ?subSource a ?subSourceType .
  FILTER(?subSourceType IN (food:PlantOrigin, food:MicrobialOrigin, food:SyntheticOrigin))
}
```

---

# **5\. Knowledge Graph Instance Data (A-Box) Requirements**

## **5.1 Ingredients Catalog (Minimum 20-25 Instances)**

The system A-Box must contain a rich catalog of raw materials, E-numbers, processing aids, and sub-ingredients. The table below details a core subset:

| Ingredient IRI                   | E-Number | Biological / Byproduct Source      | Ethanol % | Certificates                       | Functional Role    |
| :------------------------------- | :------- | :--------------------------------- | :-------- | :--------------------------------- | :----------------- |
| `food:PorcineGelatin`            | \-       | `Porcine (AnimalOrigin)`           | 0.0%      | None                               | `GellingAgent`     |
| `food:BovineGelatin`             | \-       | `Bovine (AnimalOrigin)`            | 0.0%      | `food:HalalCert_01`                | `GellingAgent`     |
| `food:AgarAgar`                  | E406     | `PlantOrigin (Seaweed)`            | 0.0%      | `food:HalalCert_02, KosherCert_01` | `GellingAgent`     |
| `food:Pectin`                    | E440     | `PlantOrigin (Citrus)`             | 0.0%      | `food:HalalCert_03, KosherCert_02` | `GellingAgent`     |
| `food:MonoAndDiglycerides`       | E471     | `AnimalFat / PlantOrigin`          | 0.0%      | None                               | `Emulsifier`       |
| `food:SoyLecithin`               | E322     | `PlantOrigin (Soy)`                | 0.0%      | `food:HalalCert_04, KosherCert_03` | `Emulsifier`       |
| `food:LCysteine`                 | E920     | `Porcine / Human Hair / Synthetic` | 0.0%      | None                               | `DoughConditioner` |
| `food:MicrobialTransglutaminase` | \-       | `MicrobialOrigin`                  | 0.0%      | `food:HalalCert_05, KosherCert_04` | `DoughConditioner` |
| `food:Carmine`                   | E120     | `Insect (Cochineal)`               | 0.0%      | None                               | `Coloring`         |
| `food:AlluraRed`                 | E129     | `SyntheticOrigin`                  | 0.0%      | `food:HalalCert_06`                | `Coloring`         |
| `food:VanillaExtract`            | \-       | `PlantOrigin`                      | 1.2%      | None                               | `Flavoring`        |
| `food:SyntheticVanilla`          | \-       | `SyntheticOrigin`                  | 0.0%      | `food:HalalCert_07`                | `Flavoring`        |
| `food:AnimalRennet`              | \-       | `AnimalEnzyme (Bovine)`            | 0.0%      | None                               | `Coagulant`        |
| `food:MicrobialRennet`           | \-       | `MicrobialOrigin`                  | 0.0%      | `food:HalalCert_08, KosherCert_05` | `Coagulant`        |
| `food:SweetWheyPowder`           | \-       | `Dairy (AnimalByproduct)`          | 0.0%      | `food:KosherCert_06`               | `TextureEnhancer`  |

## **5.2 Multi-Level Nesting & Product Benchmark Matrix**

The graph must feature nested supply chains up to 3+ levels deep (e.g., `ArtisanBread` \$\\rightarrow\$ DoughConditioner \$\\rightarrow\$ LCysteine_E920 \$\\rightarrow\$ Porcine). The benchmark products must trigger expected outcomes across all standards:

| Product Name               | Core & Nested Ingredients                                                             | Halal                      | Kosher                    | Veg      | Vegan            |
| :------------------------- | :------------------------------------------------------------------------------------ | :------------------------- | :------------------------ | :------- | :--------------- |
| **Strawberry Gummy Candy** | Gelatin (`PorcineGelatin`), Carmine (`E120`), Glucose Syrup.                          | **Fail (Porcine, Insect)** | **Fail (Treif)**          | **Fail** | **Fail**         |
| **Beef Cheese Burger**     | Beef Patty (`Bovine`, no cert), Cheddar (`Dairy`, `AnimalRennet`), Bun (`LCysteine`). | **Audit (Uncert Beef)**    | **Fail (Basar BeChalav)** | **Fail** | **Fail**         |
| **Artisan Dough Bread**    | Flour, Water, Dough Conditioner (`LCysteine` \$\\rightarrow\$ `Porcine`).             | **Fail (Porcine)**         | **Fail (Uncert)**         | **Pass** | **Pass**         |
| **Plant-Based Ramen**      | Noodle, Broth, E406 (`AgarAgar`), E322 (`SoyLecithin`).                               | **Pass**                   | **Pass**                  | **Pass** | **Pass**         |
| **Whey Protein Bar**       | Whey Powder (`Dairy`, Kosher cert), Soy Protein, Honey.                               | **Pass**                   | **Pass**                  | **Pass** | **Fail (Honey)** |
| **Vanilla Pastry**         | Flour, Butter (`Dairy`), Vanilla Extract (`Ethanol` 1.2%).                            | **Fail (Ethanol \>0.5%)**  | **Pass**                  | **Pass** | **Fail (Dairy)** |

## **5.3 Dynamic UI Custom Instantiation**

In addition to pre-loaded benchmark products, the application must provide interactive UI controls allowing end-users to construct custom recipes on the fly, link sub-ingredients, set ethanol percentages, and dynamically execute the SPARQL inference engine.

---

# **6\. Functional Requirements & Three Core Use-Cases**

```
+-----------------------------------------------------------------------------------+
|                            APPLICATION USE-CASE MODULES                           |
+-----------------------------------------------------------------------------------+
|  [Use-Case 1]                    | [Use-Case 2]          | [Use-Case 3]           |
|  Compliance Scorecard            | Graph Traceability    | Reformulation Advisor  |
|  ------------------              | ------------------    | ---------------------  |
|  Multi-standard pass/fail matrix | Transitive node-edge  | Target standard filter |
|  & diagnostic issue reports.     | supply chain visual.  | & substitute candidate |
|                                  |                       | matching engine.       |
+-----------------------------------------------------------------------------------+
```

## **6.1 Use-Case 1: Multi-Standard Product Compliance Matrix**

- **User Input:** Select an existing benchmark `FoodProduct` or assemble a dynamic ingredient list via the UI.
- **Processing Execution:** The `rdflib` engine runs Rule Sets A, B, and C against the selected product's transitive ingredient graph.
- **Output Display:**
  - Summary status card grid displaying status per standard: **Pass** (Green), **Audit Required** (Yellow), or **Fail** (Red).
  - Expandable diagnostic panel displaying inferred `ComplianceIssue` nodes, listing the offending ingredient, deep-tier parent, and violated policy text.

## **6.2 Use-Case 2: Transitive Supply Chain & Sub-Ingredient Traceability Explorer**

- **User Input:** Select a multi-tiered processed product (e.g., `Artisan Dough Bread`).
- **Processing Execution:** Execute a recursive SPARQL property path query (`food:containsIngredient+`) to extract the entire bill-of-materials tree down to primary `BiologicalOrigin` and `Certificate` nodes.
- **Output Display:**
  - Interactive, color-coded node-edge graph visualization using `streamlit-agraph`.
  - Node styles: Blue \= Finished Product, Orange \= Intermediate Ingredient, Red \= Flagged Sub-Ingredient, Green \= Valid Certificate, Grey \= Biological Origin.
  - Clicking a node opens a side panel detailing raw properties (e.g., ethanol content, E-number, taxonomic class).

## **6.3 Use-Case 3: Cross-Standard Ingredient Substitution Advisor**

- **User Input:** Select a non-compliant product and check target compliance goals (e.g., "Convert to Halal and Vegan compliant").
- **Processing Execution:**
  1. Identify non-compliant leaf ingredients triggered in Use-Case 1\.
  2. Query their `FunctionalRole`.
  3. Execute Rule Set D to evaluate candidate substitutes sharing the same `FunctionalRole` that satisfy all selected target standards.
- **Output Display:**
  - Reformulation table mapping original offending ingredients to recommended compliant alternatives (e.g., replacing `PorcineGelatin` with `AgarAgar` for Gelling Role).
  - "Simulate Reformulation" button that dynamically creates an updated virtual product instance and re-runs Use-Case 1 to verify 100% compliance.

---

# **7\. Repository Structure, Team Roles & 3-Day Sprint Schedule**

## **7.1 Modular Repository Directory Structure**

```
food-compliance-expert-system/
├── README.md
├── requirements.txt
├── app.py
├── ontology/
│   ├── food_compliance_tbox.ttl
│   └── food_compliance_abox.ttl
├── rules/
│   ├── halal_rules.sparql
│   ├── kosher_rules.sparql
│   ├── vegan_rules.sparql
│   └── substitution_rules.sparql
├── src/
│   ├── __init__.py
│   ├── knowledge_engine.py
│   ├── graph_visualizer.py
│   └── utils.py
└── reports/
    └── Technical_Report.pdf
```

## **7.2 Team Roles & Responsibilities**

| Role                                | Member Focus               | Key Deliverables                                                                                                      |
| :---------------------------------- | :------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **Member 1: Knowledge Engineer**    | T-Box & A-Box Modeling     | Protégé Turtle schema, hierarchy taxonomy, complete A-Box dataset with 25+ ingredients and nested supply chain trees. |
| **Member 2: Reasoning Engine Lead** | SPARQL & Inference         | Writing and validating SPARQL CONSTRUCT rule sets, building `rdflib` execution pipeline in `knowledge_engine.py`.     |
| **Member 3: Frontend & Web Lead**   | UI, Visualization & Report | Streamlit dashboard, `streamlit-agraph` visualizer, Cloud deployment, and compiling the final technical report.       |

## **7.3 3-Day Execution Timeline**

```
Day 1: Base Architecture & Schema
[M1] Protégé T-Box Schema Lock ------------------------------>
[M2] RDFLib Pipeline & Basic SPARQL ------------------------->
[M3] Streamlit UI Skeleton & Layout ------------------------->

Day 2: Core Engineering & Integration
[M1] Populate Full A-Box Dataset (25+ Ings) ----------------->
[M2] Implement Full SPARQL CONSTRUCT Rules ------------------->
[M3] Integrate Graph Visualizer & App Modules --------------->

Day 3: QA, Deployment & Documentation
[M1/M2] System QA & Edge-Case Testing ---------------------->
[M3] Deploy to Streamlit Cloud & Compile PDF Report --------->
```

- **Day 1: Schema Lock, Base Graph & UI Skeleton**
  - _M1:_ Draft and finalize OWL T-Box in Protégé; define classes, object/data properties, and namespaces.
  - _M2:_ Build Python `rdflib` wrapper scripts to load ontologies and run basic graph queries.
  - _M3:_ Initialize GitHub repository, set up Streamlit layout, navigation, and sidebar controls.
- **Day 2: Full Rule Engine, Complete A-Box & Integration**
  - _M1:_ Construct complete A-Box graph containing 25+ ingredients, multi-level nesting, E-numbers, and certificates.
  - _M2:_ Write and test SPARQL CONSTRUCT rules for Halal, Kosher, Vegan, and Substitution reasoning.
  - _M3:_ Connect inference engine outputs to Streamlit; implement `streamlit-agraph` for supply chain visualization.
- **Day 3: QA Testing, Cloud Deployment & Final Report**
  - _M1 & M2:_ Run validation test suites across benchmark products; fix edge cases in transitive rule inference.
  - _M3:_ Deploy application to Streamlit Community Cloud; verify live URL; compile final PDF report and submit repository.

---

# **8\. Submission Checklist & Acceptance Criteria**

## **8.1 Deliverables Checklist**

- [ ] **GitHub Repository:** Publicly accessible, cleanly structured repository containing all source code, `.ttl` ontology files, `.sparql` rule files, and a comprehensive `README.md`.
- [ ] **Live Deployed Web Application:** Working URL hosted on Streamlit Community Cloud with zero execution errors.
- [ ] **Ontology Completeness (T-Box & A-Box):** Validated Turtle files containing full taxonomy, properties, 25+ ingredients, nested products, and certificates.
- [ ] **Inference Engine Verification:** Execution of SPARQL CONSTRUCT rules successfully generating `isNonCompliantWith`, `requiresAuditFor`, and `ComplianceIssue` nodes.
- [ ] **Three Interactive Use-Cases:**
  - [ ] Use-Case 1: Compliance scorecard and diagnostic issue breakdown.
  - [ ] Use-Case 2: Interactive supply chain graph traversal visualization.
  - [ ] Use-Case 3: Automated reformulation and substitute recommendation module.
- [ ] **Final Technical Report (.pdf):** Executive-ready PDF report containing system architecture, ontology diagrams, SPARQL rule listings, use-case screenshots, and public web links.

## **8.2 Quality Acceptance Criteria**

1. **Determinism:** The rule engine must yield 100% consistent compliance determinations across all benchmark test products.
2. **Transitivity:** The system must successfully catch non-compliant sub-ingredients nested 3+ levels deep within product supply chains.
3. **Performance:** In-memory SPARQL CONSTRUCT query evaluation and UI rendering must complete within under 2 seconds per request.
4. **Usability:** The web application must provide intuitive navigation, clear visual indicators (green/yellow/red), and readable diagnostic error messages.
