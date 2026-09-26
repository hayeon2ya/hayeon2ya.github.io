
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch


# ============================================================
# Load frozen training preprocessing artifacts
# ============================================================

def load_artifacts(
    path="preprocessing_artifacts.json"
):

    return json.loads(
        Path(
            path
        ).read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# Static preprocessing
# ============================================================

def preprocess_static(
    df,
    artifacts
):

    df = df.copy()

    df.columns = [
        str(c)
        .strip()
        .lower()

        for c
        in df.columns
    ]

    z = pd.DataFrame({

        "stay_id":
            pd.to_numeric(
                df[
                    "stay_id"
                ],
                errors="raise"
            )
            .astype(
                np.int64
            )
    })


    # Numeric
    for c in artifacts[
        "numeric"
    ]:

        x = pd.to_numeric(
            df[c],
            errors="coerce"
        )

        med = float(
            artifacts[
                "numeric_stats"
            ][c][
                "median"
            ]
        )

        iqr = float(
            artifacts[
                "numeric_stats"
            ][c][
                "iqr"
            ]
        )

        z[
            c
            + "__missing"
        ] = (
            x.isna()
            .astype(
                np.float32
            )
        )

        z[c] = (

            (
                x.fillna(
                    med
                )
                - med
            )

            / iqr

        ).astype(
            np.float32
        )


    # Binary
    for c in artifacts[
        "binary"
    ]:

        z[c] = (
            pd.to_numeric(
                df[c],
                errors="coerce"
            )
            .fillna(0)
            .clip(0, 1)
            .astype(
                np.float32
            )
        )


    # Categorical
    for c in artifacts[
        "categorical"
    ]:

        vals = (

            df[c]
            .astype(
                "string"
            )
            .fillna(
                "<MISSING>"
            )
            .str.strip()
        )

        vocab = (
            artifacts[
                "categorical_vocab"
            ][c]
        )

        z[
            c
            + "_id"
        ] = (
            vals
            .map(
                vocab
            )
            .fillna(0)
            .astype(
                np.int64
            )
        )


    return z


# ============================================================
# Event preprocessing
# ============================================================

def _encode(
    series,
    vocab
):

    x = (
        series
        .astype(
            "string"
        )
        .fillna(
            "<MISSING>"
        )
        .str.strip()
    )

    return (
        x.map(
            vocab
        )
        .fillna(0)
        .astype(
            np.int32
        )
    )


def preprocess_events(
    df,
    artifacts,

    stay_col="stay_id",
    name_col="event_name",
    type_col="event_type",
    value_col="event_value",
    time_col="time_from_landmark_min",
    delta_event_col="delta_event_min",
    delta_feature_col="delta_feature_min",
    unit_col="event_unit"
):

    df = df.copy()

    df.columns = [
        str(c)
        .strip()
        .lower()

        for c
        in df.columns
    ]

    names = (

        df[
            name_col
        ]

        .astype(
            "string"
        )

        .fillna(
            "<MISSING>"
        )

        .str.strip()
    )


    values = pd.to_numeric(
        df[
            value_col
        ],
        errors="coerce"
    )


    time_min = pd.to_numeric(
        df[
            time_col
        ],
        errors="coerce"
    )


    value_stats = artifacts[
        "event_value_stats"
    ]


    med = names.map(

        lambda x:
            value_stats
            .get(
                str(x),
                {
                    "median": 0.0,
                    "iqr": 1.0
                }
            )[
                "median"
            ]
    ).astype(
        float
    )


    iqr = names.map(

        lambda x:
            value_stats
            .get(
                str(x),
                {
                    "median": 0.0,
                    "iqr": 1.0
                }
            )[
                "iqr"
            ]
    ).astype(
        float
    )


    iqr = iqr.mask(
        (~np.isfinite(iqr))
        |
        (iqr == 0),
        1.0
    )


    clip = float(
        artifacts[
            "event_clip"
        ]
    )


    z = pd.DataFrame({

        "stay_id":
            pd.to_numeric(
                df[
                    stay_col
                ],
                errors="coerce"
            ),

        "event_name_id":
            _encode(
                df[
                    name_col
                ],
                artifacts[
                    "event_name_vocab"
                ]
            ),

        "event_type_id":
            _encode(
                df[
                    type_col
                ],
                artifacts[
                    "event_type_vocab"
                ]
            ),

        "event_unit_id":
            (
                _encode(
                    df[
                        unit_col
                    ],
                    artifacts[
                        "event_unit_vocab"
                    ]
                )

                if (
                    unit_col
                    in df.columns
                )

                else np.zeros(
                    len(df),
                    dtype=np.int32
                )
            ),

        "event_value_scaled":
            np.clip(

                (
                    values
                    .fillna(
                        med
                    )
                    - med
                )

                / iqr,

                -clip,
                clip

            ).astype(
                np.float32
            ),

        "event_value_missing":
            values
            .isna()
            .astype(
                np.float32
            ),

        "time_min":
            time_min
            .astype(
                np.float32
            ),
    })


    if (
        delta_event_col
        in df.columns
    ):

        z[
            "delta_event_log"
        ] = (

            np.log1p(

                pd.to_numeric(
                    df[
                        delta_event_col
                    ],
                    errors="coerce"
                )

                .clip(
                    lower=0
                )

                .fillna(0)
            )

            .astype(
                np.float32
            )
        )

    else:

        z[
            "delta_event_log"
        ] = np.zeros(
            len(df),
            dtype=np.float32
        )


    if (
        delta_feature_col
        in df.columns
    ):

        z[
            "delta_feature_log"
        ] = (

            np.log1p(

                pd.to_numeric(
                    df[
                        delta_feature_col
                    ],
                    errors="coerce"
                )

                .clip(
                    lower=0
                )

                .fillna(0)
            )

            .astype(
                np.float32
            )
        )

    else:

        z[
            "delta_feature_log"
        ] = np.zeros(
            len(df),
            dtype=np.float32
        )


    # actual model time feature
    z[
        "time_log"
    ] = (

        np.sign(
            z[
                "time_min"
            ]
        )

        *

        np.log1p(
            np.abs(
                z[
                    "time_min"
                ]
            )
        )

    ).astype(
        np.float32
    )


    z = z[
        np.isfinite(
            z[
                "time_min"
            ]
        )
    ].copy()


    return z


# ============================================================
# Decision-specific history
# ============================================================

def select_history(
    events,
    stay_id,
    decision_min,
    max_events=256
):

    g = events[

        (
            events[
                "stay_id"
            ]
            == int(
                stay_id
            )
        )

        &

        (
            events[
                "time_min"
            ]
            <= float(
                decision_min
            )
        )

    ].sort_values(
        "time_min"
    )


    return (
        g.tail(
            int(
                max_events
            )
        )
        .copy()
    )


# ============================================================
# Dynamic collate
#
# Same convention as original training:
# - variable event history
# - batch padded to longest real sequence
# - right alignment
# - seq_mask=True only for real events
# ============================================================

_EVENT_LONG_KEYS = [
    "event_name",
    "event_type",
    "event_unit"
]

_EVENT_FLOAT_KEYS = [
    "event_value",
    "value_missing",
    "time_log",
    "delta_event",
    "delta_feature"
]


def dynamic_collate(
    batch
):

    B = len(
        batch
    )

    lengths = np.asarray(
        [
            x[
                "seq_len"
            ]
            for x
            in batch
        ],
        dtype=np.int64
    )

    L = max(
        int(
            lengths.max()
        )
        if len(
            lengths
        )
        else 0,
        1
    )


    out = {

        "static_cont":
            torch.stack(
                [
                    x[
                        "static_cont"
                    ]
                    for x
                    in batch
                ]
            ),

        "static_cat":
            torch.stack(
                [
                    x[
                        "static_cat"
                    ]
                    for x
                    in batch
                ]
            ),

        "current_state":
            torch.tensor(
                [
                    x[
                        "current_state"
                    ]
                    for x
                    in batch
                ],
                dtype=torch.long
            ),

        "stay_id":
            torch.tensor(
                [
                    x[
                        "stay_id"
                    ]
                    for x
                    in batch
                ],
                dtype=torch.long
            ),

        "decision_min":
            torch.tensor(
                [
                    x[
                        "decision_min"
                    ]
                    for x
                    in batch
                ],
                dtype=torch.float32
            ),

        "seq_len":
            torch.tensor(
                lengths,
                dtype=torch.long
            )
    }


    # Targets are optional for external inference
    if (
        "targets"
        in batch[0]
    ):

        out[
            "targets"
        ] = torch.stack(
            [
                x[
                    "targets"
                ]
                for x
                in batch
            ]
        )


    if (
        "risk_masks"
        in batch[0]
    ):

        out[
            "risk_masks"
        ] = torch.stack(
            [
                x[
                    "risk_masks"
                ]
                for x
                in batch
            ]
        )


    for k in (
        _EVENT_LONG_KEYS
    ):

        out[k] = torch.zeros(
            (
                B,
                L
            ),
            dtype=torch.long
        )


    for k in (
        _EVENT_FLOAT_KEYS
    ):

        out[k] = torch.zeros(
            (
                B,
                L
            ),
            dtype=torch.float32
        )


    out[
        "value_missing"
    ].fill_(
        1.0
    )


    out[
        "seq_mask"
    ] = torch.zeros(
        (
            B,
            L
        ),
        dtype=torch.bool
    )


    for i, x in enumerate(
        batch
    ):

        n = int(
            x[
                "seq_len"
            ]
        )

        if n == 0:
            continue


        # right-aligned
        sl = slice(
            L - n,
            L
        )


        for k in (
            _EVENT_LONG_KEYS
        ):

            out[k][
                i,
                sl
            ] = x[k]


        for k in (
            _EVENT_FLOAT_KEYS
        ):

            out[k][
                i,
                sl
            ] = x[k]


        out[
            "seq_mask"
        ][
            i,
            sl
        ] = True


    return out
