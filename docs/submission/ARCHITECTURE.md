# EcoSplice architecture

```mermaid
flowchart TD
    U[User DNA or one FASTA record] --> R[Green React dashboard]
    R -->|Same origin HTTP on localhost| A[FastAPI input and run APIs]
    A --> V[Strict validation and coordinate rules]
    V --> E[Exhaustive or filtered or adaptive engine]
    M[Saved NumPy model coefficients and frozen settings] --> E
    E --> T[Predictions and actual routes and measured work]
    T --> S[(SQLite local saved runs)]
    S --> R
    S --> X[Shared CSV and JSON and HTML report renderer]
    X --> U
    F[Frozen held-out evaluation and reference experiments] --> A
    L[One Python localhost process] --> R
    L --> A
```

The production launcher serves built React files and the API on the same loopback port. React handles presentation and request state. Python validates DNA, loads the saved coefficients once at service startup, runs inference and measures the computation. SQLite preserves scientific snapshots; repeated comparisons attach to the selected snapshot. Reports read that stored record using one shared selection contract.

Data preparation and scikit-learn training happen separately during development. They generate the saved numeric coefficients, manifests, labelled demonstrations and evaluation JSON. Application startup has no training, source downloads or remote inference dependency. The diagram's model/evaluation files are immutable scientific artifacts; the local database is writable user history.
