# Copyright 2020 The T5 Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Utilities for Question Answering (QA) evaluation.

Based on the SQuAD (v1.1) and TriviaQA (v1.0) evaluation scripts:
https://worksheets.codalab.org/rest/bundles/0x5d2ee15e3f2d4e34bb864df4955274e8/contents/blob/evaluate.py
https://github.com/mandarjoshi90/triviaqa/blob/master/evaluation/triviaqa_evaluation.py
"""

import collections
import re
import string

from absl import logging
import numpy as np


def _normalize_answer(text, to_whitespace_chars=string.punctuation):
  """Lower text and remove punctuation, articles and extra whitespace."""

  def remove_articles(s):
    return re.sub(r"\b(a|an|the)\b", " ", s)

  def replace_chars_with_whitespace(s):
    exclude = set(to_whitespace_chars)
    return "".join(" " if ch in exclude else ch for ch in s)

  def white_space_fix(s):
    return " ".join(s.split())

  text = text.lower()
  text = replace_chars_with_whitespace(text)
  text = remove_articles(text)
  text = white_space_fix(text)

  return text


def normalize_trivia_qa(answer):
  """Normalization used in official TriviaQA evaluation script."""
  return _normalize_answer(
      answer, to_whitespace_chars=string.punctuation + "‘’´`_").strip()


def normalize_squad(answer):
  """Normalization used in official SQuAD evaluation script."""
  return _normalize_answer(answer)


def _metric_max_over_ground_truths(metric_fn, prediction, ground_truths):
  return max(
      metric_fn(prediction, ground_truth) for ground_truth in ground_truths
  )


def _exact_match_score(target, prediction):
  return target == prediction


def _f1_score(target, prediction):
  """Computes token f1 score for a single target and prediction."""
  prediction_tokens = prediction.split()
  target_tokens = target.split()
  common = (collections.Counter(prediction_tokens) &
            collections.Counter(target_tokens))
  num_same = sum(common.values())
  if num_same == 0:
    return 0
  precision = 1.0 * num_same / len(prediction_tokens)
  recall = 1.0 * num_same / len(target_tokens)
  f1 = (2 * precision * recall) / (precision + recall)
  return f1


def qa_metrics(targets, predictions):
  """Computes exact match and f1 QA scores, expecting pre-normalized text."""
  if len(targets) != len(predictions):
    raise ValueError("Number of targets and predictions must match.")
  em = np.mean([
      _metric_max_over_ground_truths(_exact_match_score, p, t)
      for p, t in zip(predictions, targets)
  ])
  f1 = np.mean([
      _metric_max_over_ground_truths(_f1_score, p, t)
      for p, t in zip(predictions, targets)
  ])
  em *= 100
  f1 *= 100
  logging.info("EM = %.2f, F1 = %.2f", em, f1)
  return {"em": em, "f1": f1}
