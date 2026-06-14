;; Compatible with tree-sitter-language-pack Julia grammar.

(module_definition
  name: (identifier) @name.definition.module) @definition.module

(struct_definition
  (type_head (identifier) @name.definition.class)) @definition.class

(abstract_definition
  (type_head (identifier) @name.definition.class)) @definition.class

(function_definition
  (signature (call_expression (identifier) @name.definition.function))) @definition.function

(assignment
  (call_expression (identifier) @name.definition.function)) @definition.function

(macro_definition
  (signature (call_expression (identifier) @name.definition.macro))) @definition.macro

(call_expression
  (identifier) @name.reference.call) @reference.call
