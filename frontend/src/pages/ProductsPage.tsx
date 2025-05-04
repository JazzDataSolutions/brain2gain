export default function ProductsPage() {
  const { list, create } = useProducts();
  return (
    <Section title="Productos">
      <ProductTable data={list.data ?? []} loading={list.isLoading} />
      <ProductDialog onSave={create.mutate} />
    </Section>
  );
}

