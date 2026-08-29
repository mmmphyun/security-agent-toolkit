import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const statusSchema = z
  .union([z.array(z.string()), z.string()])
  .transform((value) => (Array.isArray(value) ? value : value.split(","))
    .map((status) => status.trim())
    .filter(Boolean))
  .refine((items) => new Set(items).size === items.length, {
    message: "status values must be unique",
  });

const tagSchema = z
  .union([z.array(z.string()), z.string()])
  .transform((value) => (Array.isArray(value) ? value : value.split(","))
    .map((tag) => tag.trim())
    .filter(Boolean))
  .refine((items) => new Set(items).size === items.length, {
    message: "tags must be unique",
  });

const pageCoverSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("color"),
    value: z.string().regex(/^#[0-9a-fA-F]{6}$/, "cover color must be a six-digit hex value"),
    position: z.coerce.number().min(0).max(100).optional(),
  }),
  z.object({
    type: z.literal("image"),
    value: z.string().trim().min(1),
    position: z.coerce.number().min(0).max(100).optional(),
  }),
]);

const pageAppearanceSchema = z.object({
  icon: z.string().trim().min(1).optional(),
  cover: pageCoverSchema.optional(),
});

const blogSchema = z.object({
  title: z.string(),
  slug: z.string().optional(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  heroImage: z.string().optional(),
  status: statusSchema.optional().default(["Published"]),
  category: z.string().optional().default("Security Automation"),
  tags: tagSchema.optional().default([]),
  page: pageAppearanceSchema.optional(),
  blocks: z.array(z.unknown()).optional().default([]),
});

export type BlogSchema = z.infer<typeof blogSchema>;

const blogCollection = defineCollection({
  loader: glob({ base: "../docs/posts", pattern: "**/*.md" }),
  schema: blogSchema,
});

export const collections = {
  blog: blogCollection,
};
