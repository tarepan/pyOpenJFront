"""Utilities."""


def merge_njd_marine_features(njd_features, marine_results):
    """Merge Open JTalk NJD features with MARINE features."""
    features = []

    marine_accs = marine_results["accent_status"]
    marine_chain_flags = marine_results["accent_phrase_boundary"]

    msg = "Invalid sequence sizes in njd_results, marine_results"
    assert len(njd_features) == len(marine_accs) == len(marine_chain_flags), msg

    for node_index, njd_feature in enumerate(njd_features):
        _feature = {}
        for feature_key in njd_feature.keys():
            if feature_key == "acc":
                _feature["acc"] = int(marine_accs[node_index])
            elif feature_key == "chain_flag":
                _feature[feature_key] = int(marine_chain_flags[node_index])
            else:
                _feature[feature_key] = njd_feature[feature_key]
        features.append(_feature)
    return features
