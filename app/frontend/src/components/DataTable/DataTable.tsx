interface DataTableProps {
	data?: Record<string, string | boolean | number>[];
}

export const DataTable = ({data}: DataTableProps) => {

	if (!data || data.length === 0) return (
		<div>			
		</div>
	);

	// From camelCase to Title Case
	const titles = Object.keys(data[0]).map((item: any) => {
		return item.replace(/([a-z])([A-Z])/g, "$1 $2");
	});

	const header = titles.map((item: any, index: number) => {
		return (
			<th key={index} className="px-6 py-4 whitespace-nowrap sticky top-0 z-10">
				{item}
			</th>
		);
	});

	// Fill cells with data
	const fillCells = (item: any) => {
		const result = [];
		const keys = Object.keys(item);

		for (let i = 0; i < keys.length; i++) {
			result.push(
				<td
					key={i}
					className={`px-6 py-4 whitespace-nowrap ${i + 1 !== keys.length ? "border-r border-slate-600/80" : ""}`}
				>
					{item[keys[i]]}
				</td>
			);
		}

		return result;
	};

	const rows = data.map((item: any, index: number) => {
		return (
			<tr className={index % 2 === 0 ? "bg-slate-800/70" : "bg-slate-900"} key={index}>
				{fillCells(item)}
			</tr>
		);
	});

	return (
		<table className="absolute w-full border-collapse">
			<thead className="uppercase text-xs text-left sticky top-0 bg-slate-900">
				<tr>{header}</tr>
			</thead>
			<tbody className="text-slate-400">{rows}</tbody>
		</table>
	);
};
