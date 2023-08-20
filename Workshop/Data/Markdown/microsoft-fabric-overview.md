---
title: What is Microsoft Fabric
description: Microsoft Fabric is an all-in-one analytics solution that covers everything from data movement to data science, Real-Time Analytics, and business intelligence.
ms.reviewer: sngun
ms.author: gesaur
author: gsaurer
ms.topic: overview
ms.custom: build-2023, build-2023-dataai, build-2023-fabric
ms.search.form: product-trident
ms.date: 05/23/2023
---

# What is Microsoft Fabric?

Microsoft Fabric is an all-in-one analytics solution for enterprises that covers everything from data movement to data science, Real-Time Analytics, and business intelligence. It offers a comprehensive suite of services, including data lake, data engineering, and data integration, all in one place.

With Fabric, you don't need to piece together different services from multiple vendors. Instead, you can enjoy a highly integrated, end-to-end, and easy-to-use product that is designed to simplify your analytics needs.

The platform is built on a foundation of Software as a Service (SaaS), which takes simplicity and integration to a whole new level.

[!INCLUDE [preview-note](../includes/preview-note.md)]

## SaaS foundation

Microsoft Fabric brings together new and existing components from Power BI, Azure Synapse, and Azure Data Explorer into a single integrated environment. These components are then presented in various customized user experiences.

:::image type="content" source="media\microsoft-fabric-overview\saas-foundation.png" alt-text="Diagram of the software as a service foundation beneath the different experiences of Fabric.":::

Fabric brings together experiences such as Data Engineering, Data Factory, Data Science, Data Warehouse, Real-Time Analytics, and Power BI onto a shared SaaS foundation. This integration provides the following advantages:

- An extensive range of deeply integrated analytics in the industry.
- Shared experiences across experiences that are familiar and easy to learn.
- Developers can easily access and reuse all assets.
- A unified data lake that allows you to retain the data where it is while using your preferred analytics tools.
- Centralized administration and governance across all experiences.

With the Microsoft Fabric SaaS experience, all the data and the services are seamlessly integrated. IT teams can centrally configure core enterprise capabilities and permissions are automatically applied across all the underlying services. Additionally, data sensitivity labels are inherited automatically across the items in the suite.

Fabric allows creators to concentrate on producing their best work, freeing them from the need to integrate, manage, or understand the underlying infrastructure that supports the experience.

## Components of Microsoft Fabric

Microsoft Fabric offers the comprehensive set of analytics experiences designed to work together seamlessly. Each experience is tailored to a specific persona and a specific task. Fabric includes industry-leading experiences in the following categories for an end-to-end analytical need.

:::image type="content" source="media\microsoft-fabric-overview\workload-menu.png" alt-text="Screenshot of the Fabric menu of experiences.":::

- **Data Engineering** - Data Engineering experience provides a world class Spark platform with great authoring experiences, enabling data engineers to perform large scale data transformation and democratize data through the lakehouse. Microsoft Fabric Spark's integration with Data Factory enables notebooks and spark jobs to be scheduled and orchestrated. For more information, see [What is Data engineering in Microsoft Fabric?](../data-engineering/data-engineering-overview.md)

- **Data Factory** - Azure Data Factory combines the simplicity of Power Query with the scale and power of Azure Data Factory. You can use more than 200 native connectors to connect to data sources on-premises and in the cloud. For more information, see [What is Data Factory in Microsoft Fabric?](../data-factory/data-factory-overview.md)

- **Data Science** - Data Science experience enables you to build, deploy, and operationalize machine learning models seamlessly within your Fabric experience. It integrates with Azure Machine Learning to provide built-in experiment tracking and model registry. Data scientists are empowered to enrich organizational data with predictions and allow business analysts to integrate those predictions into their BI reports. This way it shifts from descriptive to predictive insights. For more information, see [What is Data science in Microsoft Fabric?](../data-science/data-science-overview.md)

- **Data Warehouse** - Data Warehouse experience provides industry leading SQL performance and scale. It fully separates compute from storage, enabling independent scaling of both the components. Additionally, it natively stores data in the open Delta Lake format. For more information, see [What is data warehousing in Microsoft Fabric?](../data-warehouse/data-warehousing.md)

- **Real-Time Analytics** - Observational data, which is collected from various sources such as apps, IoT devices, human interactions, and so many more. It's currently the fastest growing data category. This data is often semi-structured in formats like JSON or Text. It comes in at high volume, with shifting schemas. These characteristics make it hard for traditional data warehousing platforms to work with. Real-Time Analytics is best in class engine for observational data analytics. For more information, see [What is Real-Time Analytics in Fabric?](../real-time-analytics/overview.md)

- **Power BI** - Power BI is the world's leading Business Intelligence platform. It ensures that business owners can access all the data in Fabric quickly and intuitively to make better decisions with data. For more information, see [What is Power BI?](/power-bi/fundamentals/power-bi-overview)

Fabric brings together all these experiences into a unified platform to offer the most comprehensive big data analytics platform in the industry.

Microsoft Fabric enables organizations, and individuals, to turn large and complex data repositories into actionable workloads and analytics, and is an implementation of data mesh architecture. To learn more about data mesh, visit the article that explains [data mesh architecture](/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/architectures/what-is-data-mesh). 

## OneLake and lakehouse - the unification of lakehouses

The Microsoft Fabric platform unifies the OneLake and lakehouse architecture across the enterprises.

### OneLake

The data lake is the foundation on which all the Fabric services are built. Microsoft Fabric Lake is also known as [OneLake](../onelake/onelake-overview.md). It's built into the Fabric service and provides a unified location to store all organizational data where the experiences operate.

OneLake is built on top of ADLS (Azure Data Lake Storage) Gen2. It provides a single SaaS experience and a tenant-wide store for data that serves both professional and citizen developers. The OneLake SaaS experience simplifies the experiences, eliminating the need for users to understand any infrastructure concepts such as resource groups, RBAC (Role-Based Access Control), Azure Resource Manager, redundancy, or regions. Additionally it doesn't require the user to even have an Azure account.

OneLake eliminates today's pervasive and chaotic data silos, which individual developers create when they provision and configure their own isolated storage accounts. Instead, OneLake provides a single, unified storage system for all developers, where discovery and data sharing is trivial and compliance with policy and security settings are enforced centrally and uniformly. For more information, see [What is OneLake?](../onelake/onelake-overview.md)

### Organizational structure of OneLake and lakehouse

OneLake is hierarchical in nature to simplify management across your organization. It's built into Microsoft Fabric and there's no requirement for any up-front provisioning. There's only one OneLake per tenant and it provides a single-pane-of-glass file-system namespace that spans across users, regions and even clouds. The data in OneLake is divided into manageable containers for easy handling.

The tenant maps to the root of OneLake and is at the top level of the hierarchy. You can create any number of workspaces within a tenant, which can be thought of as folders.

The following image shows the various Fabric items where data is stored. It's an example of how various items within Fabric would store data inside OneLake. As displayed, you can create multiple workspaces within a tenant, create multiple lakehouses within each workspace. A lakehouse is a collection of files, folders, and tables that represents a database over a data lake. To learn more, see [What is a lakehouse?](../data-engineering/lakehouse-overview.md).

:::image type="content" source="media\microsoft-fabric-overview\hierarchy-within-tenant.png" alt-text="Diagram of the hierarchy of items like lakehouses and datasets within a workspace within a tenant.":::

Every developer and business unit in the tenant can instantly create their own workspaces in OneLake. They can ingest data into their own lakehouses, start processing, analyzing, and collaborating on the data, just like OneDrive in Office.

All the Microsoft Fabric compute experiences are prewired to OneLake, just like the Office applications are prewired to use the organizational OneDrive. The experiences such as Data Engineering, Data Warehouse, Data Factory, Power BI, and Real-Time Analytics use OneLake as their native store. They don't need any extra configuration.

:::image type="content" source="media\microsoft-fabric-overview\workloads-access-data.png" alt-text="Diagram of different experiences all accessing the same OneLake data storage.":::

OneLake is designed to allow instant mounting of existing PaaS storage accounts into OneLake with the [Shortcut](../onelake/onelake-shortcuts.md) feature. There's no need to migrate or move any of the existing data. Using shortcuts, you can access the data stored in Azure Data Lake Storage.

Additionally, shortcuts allow you to easily share data between users and applications without moving or duplicating information. The shortcut capability extends to other storage systems, allowing you to compose and analyze data across clouds with transparent, intelligent caching that reduces egress costs and brings data closer to compute.

## Next steps

- [Microsoft Fabric terminology](fabric-terminology.md)
- [Create a workspace](create-workspaces.md)
- [Navigate to your items from Microsoft Fabric Home page](fabric-home.md)
- [End-to-end tutorials in Microsoft Fabric](end-to-end-tutorials.md)
