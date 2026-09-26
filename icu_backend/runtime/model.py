
import json
from pathlib import Path

import torch
import torch.nn as nn


class TimeAwareTransformer(nn.Module):

    def __init__(self, spec):

        super().__init__()

        d = int(spec["d_model"])

        self.en = nn.Embedding(
            int(spec["event_name_vocab_size"]),
            d
        )

        self.et = nn.Embedding(
            int(spec["event_type_vocab_size"]),
            d
        )

        self.eu = nn.Embedding(
            int(spec["event_unit_vocab_size"]),
            d
        )

        self.v = nn.Linear(
            1,
            d
        )

        self.miss = nn.Linear(
            1,
            d
        )

        self.time = nn.Sequential(

            nn.Linear(
                3,
                d
            ),

            nn.GELU(),

            nn.Linear(
                d,
                d
            )
        )

        self.norm = nn.LayerNorm(
            d
        )

        layer = nn.TransformerEncoderLayer(

            d_model=d,

            nhead=int(
                spec["n_heads"]
            ),

            dim_feedforward=int(
                spec["ff_dim"]
            ),

            dropout=float(
                spec["dropout"]
            ),

            activation="gelu",

            batch_first=True,

            norm_first=True
        )

        self.tr = nn.TransformerEncoder(
            layer,
            int(
                spec["n_layers"]
            )
        )

        self.scont = nn.Sequential(

            nn.Linear(
                int(
                    spec[
                        "static_cont_dim"
                    ]
                ),
                d
            ),

            nn.GELU(),

            nn.Dropout(
                float(
                    spec[
                        "dropout"
                    ]
                )
            ),

            nn.LayerNorm(
                d
            )
        )

        categorical_variables = (
            spec[
                "categorical_variables"
            ]
        )

        cards = [

            int(
                spec[
                    "categorical_cardinalities"
                ][c]
            )

            for c in
            categorical_variables
        ]

        self.cats = nn.ModuleList([

            nn.Embedding(

                x,

                min(
                    16,
                    max(
                        4,
                        int(
                            round(
                                x ** 0.25
                                * 4
                            )
                        )
                    )
                )
            )

            for x in cards
        ])

        catdim = sum(
            e.embedding_dim
            for e in self.cats
        )

        self.state = nn.Embedding(
            4,
            8
        )

        self.fuse = nn.Sequential(

            nn.Linear(
                d
                + d
                + catdim
                + 8,
                d
            ),

            nn.GELU(),

            nn.Dropout(
                float(
                    spec[
                        "dropout"
                    ]
                )
            ),

            nn.LayerNorm(
                d
            )
        )

        n_tasks = len(
            spec["tasks"]
        )

        self.heads = nn.ModuleList([

            nn.Sequential(

                nn.Linear(
                    d,
                    d // 2
                ),

                nn.GELU(),

                nn.Dropout(
                    float(
                        spec[
                            "dropout"
                        ]
                    )
                ),

                nn.Linear(
                    d // 2,
                    1
                )
            )

            for _ in range(
                n_tasks
            )
        ])


    def encode(
        self,
        b
    ):

        # Event representation
        x = (

            self.en(
                b["event_name"]
            )

            + self.et(
                b["event_type"]
            )

            + self.eu(
                b["event_unit"]
            )

            + self.v(
                b["event_value"]
                .unsqueeze(-1)
            )

            + self.miss(
                b["value_missing"]
                .unsqueeze(-1)
            )
        )

        tf = torch.stack(

            [
                b["time_log"],
                b["delta_event"],
                b["delta_feature"]
            ],

            dim=-1
        )

        x = self.norm(
            x
            + self.time(
                tf
            )
        )

        # ---------------------------------------------
        # Empty-history safety
        # ---------------------------------------------

        real_mask = (
            b["seq_mask"]
            .bool()
        )

        safe_mask = (
            real_mask
            .clone()
        )

        empty = (
            ~real_mask
            .any(
                dim=1
            )
        )

        if empty.any():

            safe_mask[
                empty,
                0
            ] = True

            x = x.clone()

            x[
                empty,
                0,
                :
            ] = 0.0


        z = self.tr(

            x,

            src_key_padding_mask=
                ~safe_mask
        )


        if not torch.isfinite(
            z
        ).all():

            raise RuntimeError(
                "Non-finite Transformer representation."
            )


        # Pool real events only
        m = (

            real_mask
            .unsqueeze(-1)
            .to(
                dtype=z.dtype
            )
        )

        hist = (

            (z * m)
            .sum(
                dim=1
            )

            /

            m.sum(
                dim=1
            )
            .clamp_min(
                1.0
            )
        )


        # Static features
        sc = self.scont(
            b[
                "static_cont"
            ]
        )


        cp = [

            e(
                b[
                    "static_cat"
                ][:, j]
            )

            for j, e
            in enumerate(
                self.cats
            )
        ]


        cat = (

            torch.cat(
                cp,
                dim=-1
            )

            if cp

            else torch.zeros(

                hist.size(0),

                0,

                dtype=
                    hist.dtype,

                device=
                    hist.device
            )
        )


        fused = self.fuse(

            torch.cat(

                [
                    hist,
                    sc,
                    cat,

                    self.state(
                        b[
                            "current_state"
                        ]
                    )
                ],

                dim=-1
            )
        )


        if not torch.isfinite(
            fused
        ).all():

            raise RuntimeError(
                "Non-finite fused representation."
            )


        return fused


    def forward(
        self,
        b
    ):

        fused = self.encode(
            b
        )

        return torch.cat(

            [
                h(
                    fused
                )
                for h
                in self.heads
            ],

            dim=1
        )


# Alias used in original notebook
Model = TimeAwareTransformer


class TransitionFineTuneModel(
    nn.Module
):

    def __init__(
        self,
        backbone,
        n_transitions=13,
        dropout=0.15
    ):

        super().__init__()

        self.backbone = (
            backbone
        )

        d = (
            backbone
            .fuse[0]
            .out_features
        )

        self.transition_head = (
            nn.Sequential(

                nn.Linear(
                    d,
                    d // 2
                ),

                nn.GELU(),

                nn.Dropout(
                    dropout
                ),

                nn.Linear(
                    d // 2,
                    n_transitions
                )
            )
        )


    def forward(
        self,
        b
    ):

        z = (
            self.backbone
            .encode(
                b
            )
        )

        return (
            self.transition_head(
                z
            )
        )


def load_spec(
    path="model_spec.json"
):

    return json.loads(
        Path(
            path
        ).read_text(
            encoding="utf-8"
        )
    )


def build_primary_model(
    spec_path="model_spec.json"
):

    spec = load_spec(
        spec_path
    )

    return Model(
        spec
    )


def build_transition_model(
    spec_path="model_spec.json"
):

    spec = load_spec(
        spec_path
    )

    backbone = Model(
        spec
    )

    return TransitionFineTuneModel(

        backbone,

        n_transitions=13,

        dropout=float(
            spec[
                "dropout"
            ]
        )
    )
