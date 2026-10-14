name: Feature request
description: Suggest a capability or a change in behaviour
labels: [enhancement]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem
      description: What are you trying to do that the tool makes hard today?
    validations:
      required: true
  - type: textarea
    id: idea
    attributes:
      label: Proposed shape
      description: If you have one. Sketches and alternatives are welcome.
    validations:
      required: false
