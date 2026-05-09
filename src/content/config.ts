import { defineCollection, z } from 'astro:content';

const patterns = defineCollection({
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date().optional(),
  }),
});

export const collections = {
  patterns,
};
